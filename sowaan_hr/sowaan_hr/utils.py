import frappe
from frappe import _
from frappe.utils import (
    flt,
    formatdate,
    get_datetime,
    getdate,
    today
)


def get_earned_leaves():
    return frappe.get_all(
        "Leave Type",
        fields=[
            "name",
            "max_leaves_allowed",
            "earned_leave_frequency",
            "rounding",
            "based_on_date_of_joining",
        ],
        filters={"is_earned_leave": 1},
    )


def get_leave_allocations(date, leave_type):
    return frappe.db.sql(
        """select name, employee, from_date, to_date, leave_policy_assignment, leave_policy
		from `tabLeave Allocation`
		where
			%s between from_date and to_date and docstatus=1
			and leave_type=%s""",
        (date, leave_type),
        as_dict=1,
    )


@frappe.whitelist()
def allocate_earned_leaves():
    """Allocate earned leaves to Employees"""
    e_leave_types = get_earned_leaves()
    today = getdate()

    for e_leave_type in e_leave_types:

        leave_allocations = get_leave_allocations(today, e_leave_type.name)

        for allocation in leave_allocations:

            if not allocation.leave_policy_assignment and not allocation.leave_policy:
                continue

            leave_policy = (
                allocation.leave_policy
                if allocation.leave_policy
                else frappe.db.get_value(
                    "Leave Policy Assignment", allocation.leave_policy_assignment, [
                        "leave_policy"]
                )
            )

            annual_allocation = frappe.db.get_value(
                "Leave Policy Detail",
                filters={"parent": leave_policy,
                         "leave_type": e_leave_type.name},
                fieldname=["annual_allocation"],
            )

            from_date = allocation.from_date

            if e_leave_type.based_on_date_of_joining:
                from_date = frappe.db.get_value(
                    "Employee", allocation.employee, "date_of_joining")

            leave_setting = frappe.get_all("Leave Type Settings", filters={
                                           "leave_type": e_leave_type.name},
                                           fields=["*"]
                                           )
            print(leave_setting, "asddfasdf")
            if len(leave_setting) > 0 and leave_setting[0].leave_frequency == "Daily":
                allocation_leave = frappe.get_all("Leave Ledger Entry", fields=[
                    "*"], filters={"employee": allocation.employee, "leave_type": e_leave_type.name})
                creation = str(allocation_leave[len(
                    allocation_leave) - 1].creation).split()
                print(creation[0], creation[0] != str(
                    getdate()), "as,dfjg allocation_leave")
                if creation[0] != str(getdate()):
                    print("hello")
                    e_leave_type.earned_leave_frequency = leave_setting[0].leave_frequency
                    update_previous_leave_allocation(
                        allocation, annual_allocation, e_leave_type)
            else:
                if check_effective_date(
                        from_date, today, e_leave_type.earned_leave_frequency, e_leave_type, allocation
                ):
                    update_previous_leave_allocation(
                        allocation, annual_allocation, e_leave_type)


def update_previous_leave_allocation(allocation, annual_allocation, e_leave_type):
    earned_leaves = get_monthly_earned_leave(
        annual_allocation, e_leave_type.earned_leave_frequency, e_leave_type.rounding
    )
    print(earned_leaves, "Eran leave")
    allocation = frappe.get_doc("Leave Allocation", allocation.name)
    new_allocation = flt(
        allocation.total_leaves_allocated) + flt(earned_leaves)

    if new_allocation > e_leave_type.max_leaves_allowed and e_leave_type.max_leaves_allowed > 0:
        new_allocation = e_leave_type.max_leaves_allowed

    if new_allocation != allocation.total_leaves_allocated:
        today_date = today()

        allocation.db_set("total_leaves_allocated",
                          new_allocation, update_modified=False)
        create_additional_leave_ledger_entry(
            allocation, earned_leaves, today_date)

        if e_leave_type.based_on_date_of_joining:
            text = _("allocated {0} leave(s) via scheduler on {1} based on the date of joining").format(
                frappe.bold(earned_leaves), frappe.bold(formatdate(today_date))
            )
        else:
            text = _("allocated {0} leave(s) via scheduler on {1}").format(
                frappe.bold(earned_leaves), frappe.bold(formatdate(today_date))
            )

        allocation.add_comment(comment_type="Info", text=text)


def check_effective_date(from_date, to_date, frequency, leave_type, allocation):
    import calendar

    from dateutil import relativedelta

    from_date = get_datetime(from_date)
    to_date = get_datetime(to_date)
    rd = relativedelta.relativedelta(to_date, from_date)
    # last day of month
    last_day = calendar.monthrange(to_date.year, to_date.month)[1]

    # print(frequency == "Daily" and modify_date[0] != str(getdate()),frequency, "as,dfjg allocation_leave")
    if (from_date.day == to_date.day and leave_type.based_on_date_of_joining) or (
            not leave_type.based_on_date_of_joining and to_date.day == last_day
    ):
        if frequency == "Monthly":
            return True
        elif frequency == "Quarterly" and rd.months % 3:
            return True
        elif frequency == "Half-Yearly" and rd.months % 6:
            return True
        elif frequency == "Yearly" and rd.months % 12:
            return True

    if frappe.flags.in_test:
        return True

    return False


def get_monthly_earned_leave(annual_leaves, frequency, rounding):
    earned_leaves = 0.0
    divide_by_frequency = {"Yearly": 1, "Half-Yearly": 6,
                           "Quarterly": 4, "Monthly": 12, "Daily": 365}
    if annual_leaves:
        earned_leaves = flt(annual_leaves) / divide_by_frequency[frequency]
        if rounding:
            if rounding == "0.25":
                earned_leaves = round(earned_leaves * 4) / 4
            elif rounding == "0.5":
                earned_leaves = round(earned_leaves * 2) / 2
            else:
                earned_leaves = round(earned_leaves)

    return earned_leaves


def create_additional_leave_ledger_entry(allocation, leaves, date):
    """Create leave ledger entry for leave types"""
    allocation.new_leaves_allocated = leaves
    allocation.from_date = date
    allocation.unused_leaves = 0
    allocation.create_leave_ledger_entry()
