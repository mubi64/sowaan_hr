# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import datetime

import frappe
from frappe import _
from frappe.utils import today
from frappe.utils import nowdate
from frappe.query_builder.functions import Max, Min, Sum
from frappe.utils import (
	add_days,
	cint,
	cstr,
	date_diff,
	flt,
	formatdate,
	get_fullname,
	get_link_to_form,
	getdate,
	nowdate,
)

#from erpnext.hr.doctype.employee.employee import get_holiday_list_for_employee

import hrms
#from hrms.hr.doctype.employee.employee import get_holiday_list_for_employee
from hrms.hr.doctype.leave_block_list.leave_block_list import get_applicable_block_dates
from hrms.hr.doctype.leave_ledger_entry.leave_ledger_entry import create_leave_ledger_entry
from hrms.hr.utils import (
	get_holiday_dates_for_employee,
	get_leave_period,
	set_employee_name,
	share_doc_with_approver,
	validate_active_employee,
)
from hrms.mixins.pwa_notifications import PWANotificationsMixin
from hrms.utils import get_employee_email

@frappe.whitelist()
def get_leave_details(employee, date=None):
	
    """
    Return exact leave details (with quarter-day precision)
    to replace HRMS's default rounding behavior.
    """
	
    if not employee:
        return {}

    date = getdate(date or nowdate())

    allocation_records = get_leave_allocation_records(employee, date)
    leave_allocation = {}
    precision = cint(frappe.db.get_single_value("System Settings", "float_precision", cache=True))

    for d in allocation_records:
        allocation = allocation_records.get(d, frappe._dict())
        remaining_leaves = get_leave_balance_on(
            employee, d, date, to_date=allocation.to_date, consider_all_leaves_in_the_allocation_period=True
        )

        end_date = allocation.to_date
        leaves_taken = get_leaves_for_period(employee, d, allocation.from_date, end_date) * -1
        leaves_pending = get_leaves_pending_approval_for_period(employee, d, allocation.from_date, end_date)
        expired_leaves = allocation.total_leaves_allocated - (remaining_leaves + leaves_taken)

        leave_allocation[d] = {
            "total_leaves": flt(allocation.total_leaves_allocated, precision),
            "expired_leaves": flt(expired_leaves, precision) if expired_leaves > 0 else 0,
            "leaves_taken": flt(leaves_taken, precision),
            "leaves_pending_approval": flt(leaves_pending, precision),
            "remaining_leaves": flt(remaining_leaves, precision),
        }

    # is used in set query
    lwp = frappe.get_list("Leave Type", filters={"is_lwp": 1}, pluck="name")

    return {
        "leave_allocation": leave_allocation,
        "leave_approver": get_leave_approver(employee),
        "lwps": lwp,
    }

def get_leave_allocation_records(employee, date, leave_type=None):
	"""Returns the total allocated leaves and carry forwarded leaves based on ledger entries"""
	Ledger = frappe.qb.DocType("Leave Ledger Entry")
	LeaveAllocation = frappe.qb.DocType("Leave Allocation")

	cf_leave_case = frappe.qb.terms.Case().when(Ledger.is_carry_forward == "1", Ledger.leaves).else_(0)
	sum_cf_leaves = Sum(cf_leave_case).as_("cf_leaves")

	new_leaves_case = frappe.qb.terms.Case().when(Ledger.is_carry_forward == "0", Ledger.leaves).else_(0)
	sum_new_leaves = Sum(new_leaves_case).as_("new_leaves")

	query = (
		frappe.qb.from_(Ledger)
		.inner_join(LeaveAllocation)
		.on(Ledger.transaction_name == LeaveAllocation.name)
		.select(
			sum_cf_leaves,
			sum_new_leaves,
			Min(Ledger.from_date).as_("from_date"),
			Max(Ledger.to_date).as_("to_date"),
			Ledger.leave_type,
			Ledger.employee,
		)
		.where(
			(Ledger.from_date <= date)
			& (Ledger.docstatus == 1)
			& (Ledger.transaction_type == "Leave Allocation")
			& (Ledger.employee == employee)
			& (Ledger.is_expired == 0)
			& (Ledger.is_lwp == 0)
			& (
				# newly allocated leave's end date is same as the leave allocation's to date
				((Ledger.is_carry_forward == 0) & (Ledger.to_date >= date))
				# carry forwarded leave's end date won't be same as the leave allocation's to date
				# it's between the leave allocation's from and to date
				| (
					(Ledger.is_carry_forward == 1)
					& (Ledger.to_date.between(LeaveAllocation.from_date, LeaveAllocation.to_date))
					# only consider cf leaves from current allocation
					& (LeaveAllocation.from_date <= date)
					& (date <= LeaveAllocation.to_date)
				)
			)
		)
	)

	if leave_type:
		query = query.where(Ledger.leave_type == leave_type)
	query = query.groupby(Ledger.employee, Ledger.leave_type)

	allocation_details = query.run(as_dict=True)

	allocated_leaves = frappe._dict()
	for d in allocation_details:
		allocated_leaves.setdefault(
			d.leave_type,
			frappe._dict(
				{
					"from_date": d.from_date,
					"to_date": d.to_date,
					"total_leaves_allocated": flt(d.cf_leaves) + flt(d.new_leaves),
					"unused_leaves": d.cf_leaves,
					"new_leaves_allocated": d.new_leaves,
					"leave_type": d.leave_type,
					"employee": d.employee,
				}
			),
		)
	return allocated_leaves

@frappe.whitelist()
def get_leave_approver(employee):
	leave_approver, department = frappe.db.get_value("Employee", employee, ["leave_approver", "department"])

	if not leave_approver and department:
		leave_approver = frappe.db.get_value(
			"Department Approver",
			{"parent": department, "parentfield": "leave_approvers", "idx": 1},
			"approver",
		)

	return leave_approver

@frappe.whitelist()
def get_leave_balance_on(
	employee: str,
	leave_type: str,
	date: datetime.date,
	to_date: datetime.date | None = None,
	consider_all_leaves_in_the_allocation_period: bool = False,
	for_consumption: bool = False,
):
	"""
	Returns leave balance till date
	:param employee: employee name
	:param leave_type: leave type
	:param date: date to check balance on
	:param to_date: future date to check for allocation expiry
	:param consider_all_leaves_in_the_allocation_period: consider all leaves taken till the allocation end date
	:param for_consumption: flag to check if leave balance is required for consumption or display
	        eg: employee has leave balance = 10 but allocation is expiring in 1 day so employee can only consume 1 leave
	        in this case leave_balance = 10 but leave_balance_for_consumption = 1
	        if True, returns a dict eg: {'leave_balance': 10, 'leave_balance_for_consumption': 1}
	        else, returns leave_balance (in this case 10)
	"""

	if not to_date:
		to_date = nowdate()

	allocation_records = get_leave_allocation_records(employee, date, leave_type)
	allocation = allocation_records.get(leave_type, frappe._dict())

	end_date = allocation.to_date if cint(consider_all_leaves_in_the_allocation_period) else date
	cf_expiry = get_allocation_expiry_for_cf_leaves(employee, leave_type, to_date, allocation.from_date)

	leaves_taken = get_leaves_for_period(employee, leave_type, allocation.from_date, end_date)

	remaining_leaves = get_remaining_leaves(allocation, leaves_taken, date, cf_expiry)

	if for_consumption:
		return remaining_leaves
	else:
		return remaining_leaves.get("leave_balance")
	
def get_leaves_for_period(
	employee: str,
	leave_type: str,
	from_date: datetime.date,
	to_date: datetime.date,
	skip_expired_leaves: bool = True,
) -> float:
	leave_entries = get_leave_entries(employee, leave_type, from_date, to_date)
	leave_days = 0

	for leave_entry in leave_entries:
		inclusive_period = leave_entry.from_date >= getdate(from_date) and leave_entry.to_date <= getdate(
			to_date
		)

		if inclusive_period and leave_entry.transaction_type == "Leave Encashment":
			leave_days += leave_entry.leaves

		elif (
			inclusive_period
			and leave_entry.transaction_type == "Leave Allocation"
			and leave_entry.is_expired
			and not skip_expired_leaves
		):
			leave_days += leave_entry.leaves

		elif leave_entry.transaction_type == "Leave Application":
			if leave_entry.from_date < getdate(from_date):
				leave_entry.from_date = from_date
			if leave_entry.to_date > getdate(to_date):
				leave_entry.to_date = to_date

			half_day = 0
			quarter_day = 0
			half_day_date = None
			# fetch half day date for leaves with half days


			if leave_entry.leaves % 1:
				half_day = 1
				half_day_date = frappe.db.get_value(
				"Leave Application", leave_entry.transaction_name, "half_day_date"
				)
			if leave_entry.leaves == 0.25 or leave_entry.leaves == -0.25 :
				quarter_day = 1
				half_day = 0
				half_day_date = None

			leave_days += (
				get_number_of_leave_day(
					employee,
					leave_type,
					leave_entry.from_date,
					leave_entry.to_date,
					quarter_day,
					half_day,
					half_day_date,
					holiday_list=leave_entry.holiday_list,
				)
				* -1
			)

	return leave_days

def get_leave_entries(employee, leave_type, from_date, to_date):
	"""Returns leave entries between from_date and to_date."""
	return frappe.db.sql(
		"""
		SELECT
			employee, leave_type, from_date, to_date, leaves, transaction_name, transaction_type, holiday_list,
			is_carry_forward, is_expired
		FROM `tabLeave Ledger Entry`
		WHERE employee=%(employee)s AND leave_type=%(leave_type)s
			AND docstatus=1
			AND (leaves<0
				OR is_expired=1)
			AND (from_date between %(from_date)s AND %(to_date)s
				OR to_date between %(from_date)s AND %(to_date)s
				OR (from_date < %(from_date)s AND to_date > %(to_date)s))
	""",
		{"from_date": from_date, "to_date": to_date, "employee": employee, "leave_type": leave_type},
		as_dict=1,
	)

@frappe.whitelist()
def get_number_of_leave_day(
	employee: str,
	leave_type: str,
	from_date: datetime.date,
	to_date: datetime.date,
	quarter_day: int | str | None = None,
	half_day: int | str | None = None,
	half_day_date: datetime.date | str | None = None,
	holiday_list: str | None = None,
) -> float:
	"""Returns number of leave days between 2 dates after considering half day and holidays
	(Based on the include_holiday setting in Leave Type)"""
	
	number_of_days = 0
	signal = 0
	la_list = frappe.get_list("Leave Application",
						   filters={
							   "employee" : employee,
							   "leave_type" : leave_type,
							   "from_date" : from_date,
							   "to_date" : to_date,
							#    "half_day" : half_day,
							#    "half_day_date" : half_day_date,
							#    "holiday_list" : holiday_list,
							   "docstatus" : 1
						   })
	# if la_list :
	# 	la_doc = frappe.get_doc("Leave Application",la_list[0].name)
	
	# 	if la_doc.custom_quarter_day == 1 :
	# 		number_of_days = 0.25
	# 		signal = 1
	if cint(quarter_day) == 1 :
		number_of_days = 0.25
		signal = 1

	if signal == 0 :	
		if cint(half_day) == 1:
			if getdate(from_date) == getdate(to_date):
				number_of_days = 0.5
			elif half_day_date and getdate(from_date) <= getdate(half_day_date) <= getdate(to_date):
				number_of_days = date_diff(to_date, from_date) + 0.5
			else:
				number_of_days = date_diff(to_date, from_date) + 1
		else:
			number_of_days = date_diff(to_date, from_date) + 1

		# if not frappe.db.get_value("Leave Type", leave_type, "include_holiday"):
		# 	number_of_days = flt(number_of_days) - flt(
		# 		get_holidays(employee, from_date, to_date, holiday_list=holiday_list)
		# 	)
	return number_of_days

def get_leaves_pending_approval_for_period(
	employee: str, leave_type: str, from_date: datetime.date, to_date: datetime.date
) -> float:
	"""Returns leaves that are pending for approval"""
	leaves = frappe.get_all(
		"Leave Application",
		filters={"employee": employee, "leave_type": leave_type, "status": "Open"},
		or_filters={
			"from_date": ["between", (from_date, to_date)],
			"to_date": ["between", (from_date, to_date)],
		},
		fields=["SUM(total_leave_days) as leaves"],
	)[0]
	return leaves["leaves"] if leaves["leaves"] else 0.0

@frappe.whitelist()
def get_holidays(employee, from_date, to_date, holiday_list=None):
	"""get holidays between two dates for the given employee"""
	if not holiday_list:
		holiday_list = get_holiday_list_for_employee(employee)

	holidays = frappe.db.sql(
		"""select count(distinct holiday_date) from `tabHoliday` h1, `tabHoliday List` h2
		where h1.parent = h2.name and h1.holiday_date between %s and %s
		and h2.name = %s""",
		(from_date, to_date, holiday_list),
	)[0][0]

	return holidays

def get_allocation_expiry_for_cf_leaves(
	employee: str, leave_type: str, to_date: datetime.date, from_date: datetime.date
) -> str:
	"""Returns expiry of carry forward allocation in leave ledger entry"""
	Ledger = frappe.qb.DocType("Leave Ledger Entry")
	expiry = (
		frappe.qb.from_(Ledger)
		.select(Ledger.to_date)
		.where(
			(Ledger.employee == employee)
			& (Ledger.leave_type == leave_type)
			& (Ledger.is_carry_forward == 1)
			& (Ledger.transaction_type == "Leave Allocation")
			& (Ledger.to_date.between(from_date, to_date))
			& (Ledger.docstatus == 1)
		)
		.limit(1)
	).run()

	return expiry[0][0] if expiry else ""
def get_remaining_leaves(
	allocation: dict, leaves_taken: float, date: str, cf_expiry: str
) -> dict[str, float]:
	"""Returns a dict of leave_balance and leave_balance_for_consumption
	leave_balance returns the available leave balance
	leave_balance_for_consumption returns the minimum leaves remaining after comparing with remaining days for allocation expiry
	"""

	def _get_remaining_leaves(remaining_leaves, end_date):
		"""Returns minimum leaves remaining after comparing with remaining days for allocation expiry"""
		if remaining_leaves > 0:
			remaining_days = date_diff(end_date, date) + 1
			remaining_leaves = min(remaining_days, remaining_leaves)

		return remaining_leaves

	if cf_expiry and allocation.unused_leaves:
		# allocation contains both carry forwarded and new leaves
		new_leaves_taken, cf_leaves_taken = get_new_and_cf_leaves_taken(allocation, cf_expiry)

		if getdate(date) > getdate(cf_expiry):
			# carry forwarded leaves have expired
			cf_leaves = remaining_cf_leaves = 0
		else:
			cf_leaves = flt(allocation.unused_leaves) + flt(cf_leaves_taken)
			remaining_cf_leaves = _get_remaining_leaves(cf_leaves, cf_expiry)

		# new leaves allocated - new leaves taken + cf leave balance
		# Note: `new_leaves_taken` is added here because its already a -ve number in the ledger
		leave_balance = (flt(allocation.new_leaves_allocated) + flt(new_leaves_taken)) + flt(cf_leaves)
		leave_balance_for_consumption = (flt(allocation.new_leaves_allocated) + flt(new_leaves_taken)) + flt(
			remaining_cf_leaves
		)
	else:
		# allocation only contains newly allocated leaves
		leave_balance = leave_balance_for_consumption = flt(allocation.total_leaves_allocated) + flt(
			leaves_taken
		)

	remaining_leaves = _get_remaining_leaves(leave_balance_for_consumption, allocation.to_date)
	return frappe._dict(leave_balance=leave_balance, leave_balance_for_consumption=remaining_leaves)

def get_new_and_cf_leaves_taken(allocation: dict, cf_expiry: str) -> tuple[float, float]:
	"""returns new leaves taken and carry forwarded leaves taken within an allocation period based on cf leave expiry"""
	cf_leaves_taken = get_leaves_for_period(
		allocation.employee, allocation.leave_type, allocation.from_date, cf_expiry
	)
	new_leaves_taken = get_leaves_for_period(
		allocation.employee, allocation.leave_type, add_days(cf_expiry, 1), allocation.to_date
	)

	# using abs because leaves taken is a -ve number in the ledger
	if abs(cf_leaves_taken) > allocation.unused_leaves:
		# adjust the excess leaves in new_leaves_taken
		new_leaves_taken += -(abs(cf_leaves_taken) - allocation.unused_leaves)
		cf_leaves_taken = -allocation.unused_leaves

	return new_leaves_taken, cf_leaves_taken