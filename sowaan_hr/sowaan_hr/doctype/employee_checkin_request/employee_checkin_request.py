# Copyright (c) 2022, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class EmployeeCheckinRequest(Document):
	def before_save(self):
		self.checkin_marked = ""
		
	def before_submit(self):
		checkin = frappe.new_doc("Employee Checkin")
		checkin.user = frappe.session.user
		checkin.employee = self.employee
		checkin.log_type = self.log_type
		checkin.time = self.time
		checkin.insert(ignore_permissions=True)
		self.checkin_marked = checkin.name

	def before_cancel(self):
		checkin = frappe.get_doc("Employee Checkin",self.checkin_marked)
		if checkin.attendance:
			frappe.throw("Attendance is already marked for this checkin request. Please cancel the attendance first if you really want to cancel this.")

		EmployeeCheckinRequest = frappe.qb.DocType("Employee Checkin Request")
		(frappe.qb.update(EmployeeCheckinRequest)
				.set("checkin_marked", "")
				.where(EmployeeCheckinRequest.name == self.name)).run()

		checkin.delete()
		self.checkin_marked = ""
		# self.save()
