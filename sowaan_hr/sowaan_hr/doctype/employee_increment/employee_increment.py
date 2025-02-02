# Copyright (c) 2024, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now, add_days


class EmployeeIncrement(Document):
	def on_submit(self):
		salary_sturcture = self.get_structure_asignment()
		tax_slab = frappe.get_last_doc("Income Tax Slab", filters={
			"company": self.company,
			"disabled": 0,
			"docstatus": 1,
			"currency": salary_sturcture.currency
		}
			)
		salary_sturcture = frappe.get_doc({
			"doctype": "Salary Structure Assignment",
			"employee": self.employee,
			"from_date": self.increment_date,
			"salary_structure": salary_sturcture.salary_structure,
			"company": self.company,
			"payroll_payable_account": salary_sturcture.payroll_payable_account,
			"currency": salary_sturcture.currency,
			"income_tax_slab": tax_slab.name,
			"base": self.revised_salary,
			"docstatus": 1
		})
		salary_sturcture.insert(ignore_permissions=True)


		# salary_slip = frappe.db.exists("Salary Slip", {
		# 		"start_date": ["<=", self.increment_date],
		# 		"end_date": [">=", self.increment_date],
		# 		"employee": self.employee
		# 	})

		# if salary_slip:
		# 	last_salary_slip = frappe.get_doc("Salary Slip", salary_slip)
			
			
		# 	start_date = last_salary_slip.start_date
		# 	end_date = last_salary_slip.end_date

		# 	end_date_ = add_days(self.increment_date, -1)

		# 	salary_slip = frappe.get_doc({
		# 		"doctype": "Salary Slip",
		# 		"employee": self.employee,
		# 		"posting_date": now(),
		# 		"payroll_frequency": last_salary_slip.payroll_frequency,
		# 		"salary_structure": salary_sturcture.salary_structure,
		# 		"start_date": start_date,
		# 		"end_date": end_date_,
		# 		"company": self.company
		# 	})
		# 	salary_slip.validate()
		# 	absent_days = frappe.utils.date_diff(end_date, end_date_) 
		# 	salary_slip.payment_days =  salary_slip.payment_days - absent_days
		# 	salary_slip.calculate_net_pay()
		# 	# print(salary_slip.as_dict().earnings, "start Date", start_date, "end date", end_date_, "salary_slip.earnings \n\n\n\n", salary_slip.custom_payment_day, salary_slip.payment_days, absent_days, salary_slip.custom_base, "\n\n")


		# 	salary_slip1 = frappe.get_doc({
		# 		"doctype": "Salary Slip",
		# 		"employee": self.employee,
		# 		"posting_date": now(),
		# 		"payroll_frequency": last_salary_slip.payroll_frequency,
		# 		"salary_structure": salary_sturcture.salary_structure,
		# 		"start_date": self.increment_date,
		# 		"end_date": end_date,
		# 		"company": self.company
		# 	})
		# 	salary_slip1.validate()

		# 	absent_days = frappe.utils.date_diff(end_date_, start_date) 
		# 	salary_slip1.payment_days =  salary_slip1.payment_days - absent_days
		# 	salary_slip1.calculate_net_pay()   
		# 	# print(salary_slip1.as_dict().earnings, "start Date", self.increment_date, "end date", end_date, "salary_slip.earnings \n\n\n\n", salary_slip1.custom_payment_day,salary_slip1.payment_days, absent_days, salary_slip1.custom_base, "\n\n") 
			
		# 	arears_amount = 0
		# 	for earning in salary_slip.earnings:
		# 		for earning1 in salary_slip1.earnings:
		# 			if earning.salary_component == earning1.salary_component:
		# 				# print(earning.amount, earning1.amount, "earning.amount \n\n\n\n")
		# 				base =  earning.amount + earning1.amount
		# 				arears_amount = arears_amount + (base - earning.amount)
		# 				break
			
		# 	from_date = add_days(end_date, 1)
		# 	end_date = frappe.call('hrms.payroll.doctype.payroll_entry.payroll_entry.get_end_date', 
		# 		frequency = last_salary_slip.payroll_frequency, 
		# 		start_date = from_date
		# 	)
		# 	arrears = frappe.get_doc({
		# 		"doctype": "Arrears Process",
		# 		"salary_component": self.arrears_salary_component,
		# 		"employee": self.employee,
		# 		"from_date": from_date,
		# 		"to_date": end_date["end_date"],
		# 		"company": self.company
		# 	})

		# 	arrears.append("arrear_process_detail", {
		# 		"employee": self.employee,
		# 		"amount": arears_amount,
		# 		"to": end_date["end_date"]
		# 	})

		# 	arrears.insert(ignore_permissions=True)

	@frappe.whitelist()
	def get_structure_asignment(self):
		
		get_last_salary_structure = frappe.get_last_doc("Salary Structure Assignment", filters=[
			["employee", "=", self.employee],
			["from_date", "<=", self.increment_date],
			["docstatus", "=", 1]
		], order_by="from_date desc")
		# print(get_last_salary_structure.base)

		return get_last_salary_structure

