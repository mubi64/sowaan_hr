# Copyright (c) 2022, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class LateApprovalRequest(Document):
	def before_save(self):
		att = frappe.get_list("Attendance", filters={
			"employee": ["=",self.employee],
			"attendance_date": ["=", self.late_date],
			"late_entry": ["=",1]
		})
		if len(att) == 0:
			frappe.throw("There is no late on the selected date.")

	def on_submit(self):
		att = frappe.get_list("Attendance", filters={
			"employee": ["=",self.employee],
			"attendance_date": ["=", self.late_date],
			"late_entry": ["=",1]
		})
		if len(att) > 0:
			att_obj = frappe.get_doc("Attendance", att[0].name)
			att_obj.cancel()
			att_obj.delete()
			frappe.db.commit()
			# self.submit()
		else:
			frappe.throw("There is no late on the selected date.")
