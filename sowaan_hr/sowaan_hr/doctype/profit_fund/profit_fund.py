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
					"is_profit_fund" : 1
 				})
			fund_contribution_doc.append("fund_contribution_entry", {
					"contribution_type": "Company",
					"amount": self.company_amount,
					"date": self.date,
					"is_profit_fund" : 1
				})
			fund_contribution_doc.save()
