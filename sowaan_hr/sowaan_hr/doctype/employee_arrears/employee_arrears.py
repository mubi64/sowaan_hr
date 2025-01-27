# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class EmployeeArrears(Document):
	def before_insert(self):
		self.create_additional_salary()

	def on_cancel(self):
		self.delete_additional_salary()



	def create_additional_salary(self):


		additional_salary = frappe.get_doc({
			'doctype': 'Additional Salary',
			'employee': self.employee,
			'salary_component': self.earning_component,  
			'amount': self.total_earning,
			'from_date': self.from_date,  
			'to_date': self.to_date,
			'is_recurring': 1,
		})
		
		additional_salary.insert()
		additional_salary.submit()

	def delete_additional_salary(self):
		additional_salary_records = frappe.get_all('Additional Salary', filters={
            'employee': self.employee,
            'salary_component': self.earning_component,
            'from_date': self.from_date,
            'to_date': self.to_date,
            'docstatus': 1  
        })
		if additional_salary_records:
			additional_salary = frappe.get_doc("Additional Salary", {"employee": self.employee, "from_date": self.from_date, "to_date": self.to_date})
			additional_salary.cancel()
			# additional_salary.delete()
