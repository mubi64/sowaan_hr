# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ProfitFund(Document):
	def before_submit(self):
		fund_contribution = frappe.get_list("Fund Contribution", filters={"employee":self.employee})
		fund_contribution_doc = frappe.get_doc("Fund Contribution", fund_contribution[0].name)

		if fund_contribution_doc:
			fund_contribution_doc.append("fund_contribution_entry", {
					"contribution_type": "Own",
					"amount": self.own_amount,
					"date": self.date,
					"is_profit_fund" : 1,
					"reference_doctype": "Profit Fund",
               		 "document_name":self.name
 				})
			fund_contribution_doc.append("fund_contribution_entry", {
					"contribution_type": "Company",
					"amount": self.company_amount,
					"date": self.date,
					"is_profit_fund" : 1,
					"reference_doctype": "Profit Fund",
                	"document_name":self.name
				})
			fund_contribution_doc.save()

	# def before_cancel(self):
	# 	fund_contribution = frappe.get_list("Fund Contribution", filters={"employee":self.employee})
	# 	fund_contribution_doc = frappe.get_doc("Fund Contribution", fund_contribution[0].name)

	# 	if fund_contribution_doc:
	# 		for i,row in enumerate(fund_contribution_doc.fund_contribution_entry):
	# 			if row.reference_doctype == "Profit Fund" and str(row.document_name) == str(self.name):
	# 				print("Working in Condition")
	# 				del fund_contribution_doc.fund_contribution_entry[i]
	# 				fund_contribution_doc.save()
	# 				# break
	def before_cancel(self):
		fund_contribution = frappe.get_list("Fund Contribution", filters={"employee": self.employee,"docstatus": 1})
		
		if fund_contribution:
			fund_contribution_doc = frappe.get_doc("Fund Contribution", fund_contribution[0].name)

			if fund_contribution_doc:
				for i in range(len(fund_contribution_doc.fund_contribution_entry) - 1, -1, -1):
					row = fund_contribution_doc.fund_contribution_entry[i]
					if row.reference_doctype == "Profit Fund" and str(row.document_name) == str(self.name):
						print("Working in Condition")
						del fund_contribution_doc.fund_contribution_entry[i]

				fund_contribution_doc.save()