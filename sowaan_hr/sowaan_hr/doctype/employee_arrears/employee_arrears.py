# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class EmployeeArrears(Document):
    pass
	# def before_insert(self):
	# 	self.create_additional_salary()
	# # 	frappe.msgprint("Bbefore_insert")
	# # 	print('bn gaya mubarak ho')

	# # def after_insert(self):
	# # 	frappe.msgprint("after_insert Insert")
	# # 	print('bn gaya mubarak ho')
	# # 	self.create_additional_salary()

	# # def before_save(self):
	# # 	frappe.msgprint("before_save Insert")
	# # 	print('bn gaya mubarak ho')

	# # def after_save(self):
	# # 	frappe.msgprint("after_save Insert")
	# # 	print('bn gaya mubarak ho')

	# # def before_submit(self):
	# # 	frappe.msgprint("before_submit Insert")
	# # 	print('bn gaya mubarak ho')

	# # def after_submit(self):
	# # 	frappe.msgprint("after_submit Insert")
	# # 	print('bn gaya mubarak ho')




	# def create_additional_salary(self):


	# 	additional_salary = frappe.get_doc({
	# 		'doctype': 'Additional Salary',
	# 		'employee': self.employee,
	# 		'salary_component': self.earning_component,  
	# 		'amount': self.total_earning,
	# 		'from_date': self.from_date,  
	# 		'to_date': self.to_date,      
	# 	})
		
	# 	additional_salary.insert()  
	# 	frappe.msgprint(f"Additional Salary for {self.employee} created successfully.")
