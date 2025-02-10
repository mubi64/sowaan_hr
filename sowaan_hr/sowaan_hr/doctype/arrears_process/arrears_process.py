# Copyright (c) 2024, Sowaan and contributors
# For license information, please see license.txt

from pydoc import doc
import frappe
from datetime import datetime
from frappe.utils import now, add_days
from frappe.model.document import Document


class ArrearsProcess(Document):
	def before_save(self):
		self.validate_arrears_process()

	def validate_arrears_process(self):
		filters = []
		employees_list = []

		if not self.for_new_employees:
			filters = [
				["from_date", ">", self.from_date],
				["from_date", "<=", self.to_date],
				["docstatus", "=", 1]
			]
			if self.company:
				filters.append(["company", "=", self.company])
			if self.department:
				filters.append(["department", "=", self.department])
			if self.employee:
				filters.append(["employee", "=", self.employee])
				employees_list = frappe.get_all("Salary Structure Assignment", filters=filters, fields=['employee'], distinct=True)
			else:
				employees_list = frappe.get_all("Employee Increment", filters=filters, fields=['employee'], distinct=True)

			filter_employee = []
			for emp in employees_list:
				emp_arrears_exit = self.get_employee_arrears(emp.employee, self.from_date, self.to_date, self.salary_component)
				if not emp_arrears_exit:
					filter_employee.append(emp)

			employees_done = []
			for emp in filter_employee:
				if frappe.db.get_value("Employee", emp.employee, "status") == "Active" and emp.employee in employees_done:
					continue
				employees_done.append(emp.employee)

				salary_structure_assignment_list = frappe.get_all("Salary Structure Assignment",
						filters=[
							["employee","=", emp.employee],
							["from_date",">", self.from_date],
							["from_date","<=", self.to_date]
						],
						fields=['name'],
				)
				if not salary_structure_assignment_list:
					continue

				salary_structure_assignment = frappe.get_doc("Salary Structure Assignment", salary_structure_assignment_list[0].name)
				
				default_salary = self.get_salary_slip(emp.employee, self.from_date, self.to_date)

				absent_days = frappe.utils.date_diff(self.to_date, add_days(salary_structure_assignment.from_date, -1))
				first_salary = self.get_salary_slip(emp.employee, self.from_date, add_days(salary_structure_assignment.from_date, -1), absent_days)
				first_salary.payment_days = first_salary.payment_days - absent_days
				first_salary.calculate_net_pay()

				sal_1_basic = 0
				for x in first_salary.earnings:
					for d in self.a_p_earnings:
						if x.salary_component == d.salary_component:
							sal_1_basic = sal_1_basic + x.amount

				second_salary = self.get_salary_slip(emp.employee, salary_structure_assignment.from_date, self.to_date)
				absent_days = frappe.utils.date_diff(salary_structure_assignment.from_date, self.from_date)
				second_salary.payment_days =  second_salary.payment_days - (absent_days)
				second_salary.calculate_net_pay()

				sal_2_basic = 0
				for x in second_salary.earnings:
					for d in self.a_p_earnings:
						if x.salary_component == d.salary_component:
							sal_2_basic = sal_2_basic + x.amount

				curr_basic = 0
				for x in default_salary.earnings:
					for d in self.a_p_earnings:
						if x.salary_component == d.salary_component:
							curr_basic = curr_basic + x.amount

				total_basic = sal_2_basic + sal_1_basic   
				arrears_basic = total_basic - curr_basic

				for row in self.arrear_process_detail:
					if row.employee == emp.employee:
						# If the condition is true, update the row
						row.to = self.to_date
						row.base_salary = salary_structure_assignment.base
						row.amount = arrears_basic
						break  # Exit the loop when a match is found
				else:
					# This block runs only if the loop completes without a 'break'
					new_row = self.append("arrear_process_detail", {})
					new_row.employee = emp.employee
					new_row.to = self.to_date
					new_row.base_salary = salary_structure_assignment.base
					new_row.amount = arrears_basic


			# for emp in employees_list:
			# 	employee_status = frappe.db.get_value("Employee", emp.employee, "status")
			# 	if employee_status == "Active" and emp.employee in employees_done:
			# 		continue

			# 	employees_done.append(emp.employee)
				
			# 	salary_structure_assignment_list = frappe.get_all("Salary Structure Assignment",
			# 			filters=[
			# 				["employee","=", emp.employee],
			# 				["from_date",">", self.from_date],
			# 				["from_date","<=", self.to_date]
			# 			],
			# 			fields = ['*'],
			# 	)
			# 	if not salary_structure_assignment_list:
			# 		continue

			# 	salary_structure_assignment = frappe.get_doc(
			# 		"Salary Structure Assignment", 
			# 		salary_structure_assignment_list[0].name
			# 	)
			
			# 	default_salary = frappe.get_doc({
			# 		"doctype": 'Salary Slip',
			# 		"employee": emp.employee,
			# 		"posting_date": self.to_date,
			# 		"payroll_frequency": "",
			# 		"start_date": self.from_date,
			# 		"end_date": self.to_date,
			# 		"docstatus": 0
			# 	})
			# 	default_salary.validate()
						
			# 	absent_days = frappe.utils.date_diff(self.to_date, salary_structure_assignment.from_date) 
			# 	# print(absent_days, self.to_date, salary_structure_assignment.from_date, "absent_days \n\n\n\n")
			# 	first_salary = frappe.get_doc({
			# 		"doctype": 'Salary Slip',
			# 		"employee": emp.employee,
			# 		"posting_date": self.to_date,
			# 		"payroll_frequency": "",
			# 		"start_date": self.from_date,
			# 		"end_date": self.to_date,
			# 		"absent_days": absent_days,
			# 		"docstatus": 0
			# 	})
			# 	first_salary.validate()
			# 	first_salary.payment_days =  first_salary.payment_days - (absent_days+1)
			# 	first_salary.calculate_net_pay()
				
			# 	sal_1_basic = 0
			# 	for x in first_salary.earnings:
			# 		# if x.salary_component == 'Basic':
			# 		sal_1_basic = sal_1_basic + x.amount
				
				
			# 	end_date = frappe.call('hrms.payroll.doctype.payroll_entry.payroll_entry.get_end_date', 
			# 		frequency = "Monthly", 
			# 		start_date = salary_structure_assignment.from_date
			# 	)
			# 	# print(end_date, "End Date \n\n\n\n\n\n")
				
			# 	second_salary = frappe.get_doc({
			# 		"doctype": 'Salary Slip',
			# 		"employee": emp.employee,
			# 		"posting_date": self.to_date,
			# 		"payroll_frequency": "",
			# 		"start_date": salary_structure_assignment.from_date,
			# 		"end_date": end_date["end_date"],
			# 		"docstatus": 0
			# 	})
			# 	second_salary.validate() 
				
			# 	absent_days = frappe.utils.date_diff(second_salary.end_date, self.to_date) 
			# 	second_salary.payment_days =  second_salary.payment_days - absent_days
			# 	second_salary.calculate_net_pay()    
				
				
			# 	sal_2_basic = 0
			# 	for x in second_salary.earnings:
			# 		# if x.salary_component == 'Basic':
			# 		sal_2_basic = sal_2_basic + x.amount
						
				
			# 	curr_basic = 0
			# 	for x in default_salary.earnings:
			# 		# if x.salary_component == 'Basic':
			# 		curr_basic = curr_basic + x.amount
					
					
			# 	total_basic = sal_2_basic + sal_1_basic

			# 	emp_arrears = frappe.get_doc({
			# 		"doctype": "Employee Arrears",
			# 		"employee": emp.employee,
			# 		"from_date": self.from_date,
			# 		"to_date": self.to_date,
			# 		"earning_component": self.salary_component,
			# 		"docstatus": 1
			# 	})  
			# 	earn_existing = []
			# 	deduct_existing = []
			# 	for x in self.a_p_earnings:
			# 		if not x.salary_component in earn_existing:
			# 			earn_existing.append(x.salary_component)
			# 			emp_arrears.append("e_a_earnings", x)

			# 	for x in self.a_p_deductions:
			# 		if not x.salary_component in deduct_existing:
			# 			deduct_existing.append(x.salary_component)
			# 			emp_arrears.append("e_a_deductions", x)
				
			# 	for f_salary in first_salary.earnings:
			# 		for s_salary in second_salary.earnings:
			# 			for d_salary in default_salary.earnings:
			# 				for c_salary in emp_arrears.e_a_earnings:
			# 					if f_salary.salary_component == s_salary.salary_component == d_salary.salary_component == c_salary.salary_component:
			# 						arrears_basic = (s_salary.amount + f_salary.amount) - d_salary.amount
			# 						c_salary.amount = arrears_basic
			# 						break

			# 	for f_salary in first_salary.deductions:
			# 		for s_salary in second_salary.deductions:
			# 			for d_salary in default_salary.deductions:
			# 				for c_salary in emp_arrears.e_a_deductions:
			# 					if f_salary.salary_component == s_salary.salary_component == d_salary.salary_component == c_salary.salary_component:
			# 						# print(f_salary.salary_component, s_salary.salary_component, d_salary.salary_component, "Deductions \n\n\n\n")
			# 						arrears_basic = (s_salary.amount + f_salary.amount) - d_salary.amount
			# 						c_salary.amount = arrears_basic
			# 						break
			# 	emp_arrears_exit = frappe.db.exists("Employee Arrears", {
			# 		"employee": emp.employee,
			# 		"from_date": self.from_date,
			# 		"to_date": self.to_date,
			# 		"earning_component": self.salary_component,
			# 	})
				
			# 	if not emp_arrears_exit:
			# 		emp_arrears.insert(ignore_permissions=True)

			# 	arrears_basic = total_basic - curr_basic
				
			# 	if len(self.arrear_process_detail) > 0:
			# 		for row in self.arrear_process_detail:
			# 			if row.employee == emp.employee:
			# 				row.to = self.to_date
			# 				row.base_salary = salary_structure_assignment.base
			# 				row.amount = arrears_basic
			# 	else:
			# 		new_row = self.append("arrear_process_detail", {})
			# 		new_row.employee = emp.employee
			# 		new_row.to = self.to_date
			# 		# new_row.base_salary = salary_structure_assignment.base
			# 		new_row.amount = arrears_basic
		
		if self.for_new_employees:
			previouse_month_from_date = frappe.utils.add_months(self.from_date, -1)
			previous_month_end_date = frappe.utils.add_months(self.to_date, -1)
			filters = [
				["date_of_joining", "Between", [previouse_month_from_date, previous_month_end_date]],
				["status", "=", "Active"]
			]
			if self.employee:
				filters.append(["name", "=", self.employee])
			new_employee = frappe.get_all("Employee", filters=filters)
			filter_employee = []
			for emp in new_employee:
				emp_arrears_exit = self.get_employee_arrears(emp.name, self.from_date, self.to_date, self.salary_component)
				if not emp_arrears_exit:
					filter_employee.append(emp)

			for emp in filter_employee:
				if (not frappe.db.exists("Salary Slip", {
					"employee": emp.name,
					"start_date": previouse_month_from_date,
					"end_date": previous_month_end_date,
				})) and frappe.db.exists("Salary Structure Assignment", {
					"employee": emp.name,
					"from_date": ["Between", [previouse_month_from_date, previous_month_end_date]],
					"company": self.company,
					"docstatus": 1
				}):
					default_salary = self.get_salary_slip(emp.name, previouse_month_from_date, previous_month_end_date)
					
					total_basic = 0
					for x in self.a_p_earnings:
						for d in default_salary.earnings:
							if x.salary_component == d.salary_component:
								total_basic = total_basic + d.amount
							
					arrears_basic = total_basic
					if emp.name in [row.employee for row in self.arrear_process_detail]:
						for row in self.arrear_process_detail:
							if row.employee == emp.name:
								# If the condition is true, update the row
								row.to = self.to_date
								row.amount = arrears_basic
								break
					else:
						self.append("arrear_process_detail", {
							"employee": emp.name,
							"to": self.to_date,
							"amount": arrears_basic
						})

	def get_employee_arrears(self, employee, from_date, to_date, salary_component):
		"""Check if Employee Arrears exists."""
		return frappe.db.exists("Employee Arrears", {
			"employee": employee,
			"from_date": from_date,
			"to_date": to_date,
			"earning_component": salary_component,
			"docstatus": 1
		})
	
	def get_salary_slip(self, employee, start_date, end_date, absent_days=None):
		salary_slip = frappe.get_doc({
			"doctype": 'Salary Slip',
			"employee": employee,
			"posting_date": end_date,
			"start_date": start_date,
			"end_date": end_date,
			"docstatus": 0
		})
		if absent_days:
			salary_slip.absent_days = absent_days
		salary_slip.validate()
		return salary_slip
	

# def add_arrears_to_earnings(doc, method):
# 	# print('hamara hai')
# 	# pass
# 	start_date = doc.start_date
# 	end_date = doc.end_date
# 	# basic_arrear = 0

# 	# arrear_process_details = frappe.get_all(
# 	# 	'Arrear Process Detail',
# 	# 	filters={
# 	# 		'employee': doc.employee,
# 	# 	}, fields=['amount'])

# def add_arrears_to_earnings(doc, method):
# 	start_date = doc.start_date
# 	end_date = doc.end_date

# 			earning_row_exists = False
# 			for row in doc.earnings:
# 				if row.salary_component == arr_process.earning_component:
# 					row.amount = er_amount
# 					# print(row.salary_component, arr_process.earning_component, row.amount, er_amount,  "arr_process.earnings \n\n\n\n")
# 					earning_row_exists = True
# 					break
# 			if not earning_row_exists:
# 				# print(arr_process.earning_component, er_amount ,'\n\n\n\n')
# 				doc.append("earnings", {
# 					"salary_component": arr_process.earning_component,
# 					"amount": er_amount
# 				})
# 				# frappe.msgprint(str(arr_process.earning_component ))
		
# 		for arr_deduction in arr_process.e_a_deductions:
# 			if arr_deduction.amount > 0:
# 				doc.append("deductions", {
# 					"salary_component": arr_deduction.salary_component,
# 					"amount": arr_deduction.amount
# 				})

# 		# doc.gross_pay = doc.gross_pay + er_amount
# 		# doc.net_pay = doc.net_pay + er_amount
# 		# doc.rounded_total = round(doc.rounded_total + er_amount)

		# 	earning_row_exists = False
		# 	for row in doc.earnings:
		# 		if row.salary_component == arr_process.earning_component:
		# 			row.amount = er_amount
		# 			earning_row_exists = True
		# 			break
		# 	if not earning_row_exists:
		# 		doc.append("earnings", {
		# 			"salary_component": arr_process.earning_component,
		# 			"amount": er_amount
		# 		})
		
		# for arr_deduction in arr_process.e_a_deductions:
		# 	if arr_deduction.amount > 0:
		# 		doc.append("deductions", {
		# 			"salary_component": arr_deduction.salary_component,
		# 			"amount": arr_deduction.amount
		# 		})

