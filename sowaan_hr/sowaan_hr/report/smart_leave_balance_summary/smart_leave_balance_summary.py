# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import (_,utils)

#from hrms.hr.doctype.leave_application.leave_application import get_leave_details
from sowaan_hr.sowaan_hr.api.leave_application import get_leave_details
#from hrms.hr.report.employee_leave_balance.employee_leave_balance import (
# 	get_department_leave_approver_map,
# )



def get_department_leave_approver_map(department = None):
	# get current department and all its child
	department_list = frappe.get_list(
		"Department",
		filters={"disabled": 0},
		or_filters={"name": department, "parent_department": department},
		pluck="name",
	)
	# retrieve approvers list from current department and from its subsequent child departments
	approver_list = frappe.get_all(
		"Department Approver",
		filters={"parentfield": "leave_approvers", "parent": ("in", department_list)},
		fields=["parent", "approver"],
		as_list=True,
	)

	approvers = {}

	for k, v in approver_list:
		approvers.setdefault(k, []).append(v)

	return approvers


def execute(filters=None):
	leave_types = frappe.db.sql_list("select name from `tabLeave Type` order by name asc")

	columns = get_columns(leave_types)
	data = get_data(filters, leave_types)

	return columns, data


def get_columns(leave_types):
	columns = [
		_("Employee") + ":Link.Employee:150",
		_("Employee Name") + "::200",
		_("Department") + "::150",
	]

	for leave_type in leave_types:
		columns.append(_(leave_type) + ":Float:160")

	return columns


def get_conditions(filters):
	conditions = {}
	if filters.get("company"):
		conditions.update({"company": filters.get("company")})
	if filters.get("employee_status"):
		conditions.update({"status": filters.get("employee_status")})
	if filters.get("department"):
		conditions.update({"department": filters.get("department")})
	if filters.get("employee"):
		conditions.update({"employee": filters.get("employee")})

	return conditions


def get_data(filters, leave_types):
	user = frappe.session.user
	conditions = get_conditions(filters)

	active_employees = frappe.get_all(
		"Employee",
		filters=conditions,
		fields=["name", "employee_name", "department", "user_id", "leave_approver"],
	)

	department_approver_map = get_department_leave_approver_map(filters.get("department"))


	data = []
	for employee in active_employees:
		leave_approvers = department_approver_map.get(employee.department, [])
		if employee.leave_approver:
			leave_approvers.append(employee.leave_approver)

		if (
			(len(leave_approvers) and user in leave_approvers)
			or (user in ["Administrator", employee.user_id])
			or ("HR Manager" in frappe.get_roles(user))
		):
			
			row = [employee.name, employee.employee_name, employee.department]
			available_leave = get_leave_details(employee.name, utils.today())
			for leave_type in leave_types:
				remaining = 0
				if leave_type in available_leave["leave_allocation"]:
					# opening balance
					remaining = available_leave["leave_allocation"][leave_type]["remaining_leaves"]

				row += [remaining]

			data.append(row)

	return data
