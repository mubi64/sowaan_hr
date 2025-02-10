# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class SowaanHRSetting(Document):
	pass
	# def before_save(self):
	# 	if self.employees:
	# 		ded_emp_list = frappe.get_list(
	# 		"Deduction Employees",
	# 		filters={
	# 			"parenttype": "Sowaan HR Setting",
	# 			"parent": ["!=", self.name]
	# 		},
	# 		fields=["employee"],
	# 		ignore_permissions=True
	# 		)

	# 		all_ded_emp_data = []

	# 		for emp in ded_emp_list:
	# 			all_ded_emp_data.append(emp.employee)

	# 		# frappe.throw(f"{all_ded_emp_data}")

	# 		for row in self.employees:
	# 			if row.employee in all_ded_emp_data:
	# 				frappe.throw(f'Employee "{row.employee}" already used in another record.')


	# 	elif self.salary_structures:
	# 		ded_ss_list = frappe.get_list(
	# 		"Deduction Salary Structures",
	# 		filters={
	# 			"parenttype": "Sowaan HR Setting",
	# 			"parent": ["!=", self.name]
	# 		},
	# 		fields=["salary_structure"],
	# 		ignore_permissions=True
	# 		)

	# 		all_ded_ss_data = []

	# 		for ss in ded_ss_list:
	# 			all_ded_ss_data.append(ss.salary_structure)


	# 		for row in self.salary_structures:
	# 			if row.salary_structure in all_ded_ss_data:
	# 				frappe.throw(f'Salary Structure "{row.salary_structure}" already used in another record.')

		# finally_list = all_ded_ss_data + all_ded_emp_data

			# frappe.throw(f"{all_ded_ss_data}")
