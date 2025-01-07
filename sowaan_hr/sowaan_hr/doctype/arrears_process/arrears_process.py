# Copyright (c) 2024, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ArrearsProcess(Document):
	def before_save(self):
		self.validate_arrears_process()

	
	def on_submit(self):
		for row in self.arrear_process_detail:
			emp_arrears_exit = frappe.db.exists("Employee Arrears", {
					"employee": row.employee,
					"from_date": self.from_date,
					"to_date": self.to_date,
					"earning_component": self.salary_component,
				})
			if emp_arrears_exit:
				frappe.db.set_value("Employee Arrears", emp_arrears_exit, "arrears_process", self.name)

	def validate_arrears_process(self):
		filters = [
			["from_date", ">", self.from_date],
			["from_date", "<=", self.to_date],
			["docstatus", "=", 1]
		]

		if self.company:
			filters.append(["company", "=", self.company])

		# if self.location:
		# 	filters.append(["location", "=", self.location])

		if self.department:
			filters.append(["department", "=", self.department])
			
		if self.employee:
			filters.append(["employee", "=", self.employee])

		employees_list = frappe.get_all(
			"Salary Structure Assignment",
			filters=filters,
			fields=['employee']
		)

		if not employees_list:
			return

		employees_done = []

		for emp in employees_list:
			employee_status = frappe.db.get_value("Employee", emp.employee, "status")
			if employee_status == "Active" and emp.employee in employees_done:
				continue

			employees_done.append(emp.employee)
			
			salary_structure_assignment_list = frappe.get_all("Salary Structure Assignment",
					filters=[
						["employee","=", emp.employee],
						["from_date",">", self.from_date],
						["from_date","<=", self.to_date]
					],
					fields = ['*'],
			)
			if not salary_structure_assignment_list:
				continue

			salary_structure_assignment = frappe.get_doc(
				"Salary Structure Assignment", 
				salary_structure_assignment_list[0].name
			)
		
			default_salary = frappe.get_doc({
				"doctype": 'Salary Slip',
				"employee": emp.employee,
				"posting_date": self.to_date,
				"payroll_frequency": "",
				"start_date": self.from_date,
				"end_date": self.to_date,
				"docstatus": 0
			})
			default_salary.validate()
					
			absent_days = frappe.utils.date_diff(self.to_date, salary_structure_assignment.from_date) 
			# print(absent_days, self.to_date, salary_structure_assignment.from_date, "absent_days \n\n\n\n")
			first_salary = frappe.get_doc({
				"doctype": 'Salary Slip',
				"employee": emp.employee,
				"posting_date": self.to_date,
				"payroll_frequency": "",
				"start_date": self.from_date,
				"end_date": self.to_date,
				"absent_days": absent_days,
				"docstatus": 0
			})
			first_salary.validate()
			first_salary.payment_days =  first_salary.payment_days - (absent_days+1)
			first_salary.calculate_net_pay()
			
			sal_1_basic = 0
			for x in first_salary.earnings:
				# if x.salary_component == 'Basic':
				sal_1_basic = sal_1_basic + x.amount
			
			
			end_date = frappe.call('hrms.payroll.doctype.payroll_entry.payroll_entry.get_end_date', 
				frequency = "Monthly", 
				start_date = salary_structure_assignment.from_date
			)
			# print(end_date, "End Date \n\n\n\n\n\n")
			
			second_salary = frappe.get_doc({
				"doctype": 'Salary Slip',
				"employee": emp.employee,
				"posting_date": self.to_date,
				"payroll_frequency": "",
				"start_date": salary_structure_assignment.from_date,
				"end_date": end_date["end_date"],
				"docstatus": 0
			})
			second_salary.validate() 
			
			absent_days = frappe.utils.date_diff(second_salary.end_date, self.to_date) 
			second_salary.payment_days =  second_salary.payment_days - absent_days
			second_salary.calculate_net_pay()    
			
			
			sal_2_basic = 0
			for x in second_salary.earnings:
				# if x.salary_component == 'Basic':
				sal_2_basic = sal_2_basic + x.amount
					
			
			curr_basic = 0
			for x in default_salary.earnings:
				# if x.salary_component == 'Basic':
				curr_basic = curr_basic + x.amount
				
				
			total_basic = sal_2_basic + sal_1_basic

			emp_arrears = frappe.get_doc({
				"doctype": "Employee Arrears",
				"employee": emp.employee,
				"from_date": self.from_date,
				"to_date": self.to_date,
				"earning_component": self.salary_component,
				"docstatus": 1
			})  
			earn_existing = []
			deduct_existing = []
			for x in self.a_p_earnings:
				if not x.salary_component in earn_existing:
					earn_existing.append(x.salary_component)
					emp_arrears.append("e_a_earnings", x)

			for x in self.a_p_deductions:
				if not x.salary_component in deduct_existing:
					deduct_existing.append(x.salary_component)
					emp_arrears.append("e_a_deductions", x)
			
			for f_salary in first_salary.earnings:
				for s_salary in second_salary.earnings:
					for d_salary in default_salary.earnings:
						for c_salary in emp_arrears.e_a_earnings:
							if f_salary.salary_component == s_salary.salary_component == d_salary.salary_component == c_salary.salary_component:
								arrears_basic = (s_salary.amount + f_salary.amount) - d_salary.amount
								c_salary.amount = arrears_basic
								break

			for f_salary in first_salary.deductions:
				for s_salary in second_salary.deductions:
					for d_salary in default_salary.deductions:
						for c_salary in emp_arrears.e_a_deductions:
							if f_salary.salary_component == s_salary.salary_component == d_salary.salary_component == c_salary.salary_component:
								# print(f_salary.salary_component, s_salary.salary_component, d_salary.salary_component, "Deductions \n\n\n\n")
								arrears_basic = (s_salary.amount + f_salary.amount) - d_salary.amount
								c_salary.amount = arrears_basic
								break
			emp_arrears_exit = frappe.db.exists("Employee Arrears", {
				"employee": emp.employee,
				"from_date": self.from_date,
				"to_date": self.to_date,
				"earning_component": self.salary_component,
			})
			
			if not emp_arrears_exit:
				emp_arrears.insert(ignore_permissions=True)

			arrears_basic = total_basic - curr_basic
			
			if len(self.arrear_process_detail) > 0:
				for row in self.arrear_process_detail:
					if row.employee == emp.employee:
						row.to = self.to_date
						row.base_salary = salary_structure_assignment.base
						row.amount = arrears_basic
			else:
				new_row = self.append("arrear_process_detail", {})
				new_row.employee = emp.employee
				new_row.to = self.to_date
				# new_row.base_salary = salary_structure_assignment.base
				new_row.amount = arrears_basic
	



def add_arrears_to_earnings(doc, method):
	# pass
	start_date = doc.start_date
	end_date = doc.end_date
	# basic_arrear = 0

	# arrear_process_details = frappe.get_all(
	# 	'Arrear Process Detail',
	# 	filters={
	# 		'employee': doc.employee,
	# 	}, fields=['amount'])


	arrears_process = frappe.get_all(
		'Employee Arrears',
		filters=[
			['from_date', '>=', start_date],
			['from_date', '<', end_date],
			['employee', '=', doc.employee]
		])

	if arrears_process:
		arr_process = frappe.get_doc('Employee Arrears', arrears_process[0].name)
		er_amount = 0
		for arr_earning in arr_process.e_a_earnings:
			er_amount = er_amount + arr_earning.amount

			earning_row_exists = False
			for row in doc.earnings:
				if row.salary_component == arr_process.earning_component:
					row.amount = er_amount
					# print(row.salary_component, arr_process.earning_component, row.amount, er_amount,  "arr_process.earnings \n\n\n\n")
					earning_row_exists = True
					break
			if not earning_row_exists:
				doc.append("earnings", {
					"salary_component": arr_process.earning_component,
					"amount": er_amount
				})
		
		for arr_deduction in arr_process.e_a_deductions:
			if arr_deduction.amount > 0:
				doc.append("deductions", {
					"salary_component": arr_deduction.salary_component,
					"amount": arr_deduction.amount
				})
	# if arrear_process_details and arrears_process:
	# 	basic_arrear = arrear_process_details[0].amount
	# 	salary_component = arrears_process[0].salary_component
		
		
		# basic_arrears_row_exists = False
		# for row in doc.earnings:
		# 	if row.salary_component == salary_component:
		# 		row.amount = basic_arrear
		# 		basic_arrears_row_exists = True
		# 		break

	# 	if not basic_arrears_row_exists:
	# 		doc.append("earnings", {
	# 			"salary_component": salary_component,
	# 			"amount": basic_arrear
	# 		})
