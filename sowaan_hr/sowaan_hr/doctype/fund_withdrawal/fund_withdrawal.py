# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class FundWithdrawal(Document):
	def before_submit(self):
		fund_contribution = frappe.get_list("Fund Contribution", filters={"employee":self.employee})
		fund_contribution_doc = frappe.get_doc("Fund Contribution", fund_contribution[0].name)
		amount = self.withdrawal_amount / 2
		own_amount = 0
		company_amount = 0
		for row in fund_contribution_doc.fund_contribution_entry:
			if row.contribution_type == "Own" and not row.is_fund_withdrawal:
				own_amount = own_amount + row.amount
			if row.contribution_type == "Company" and not row.is_fund_withdrawal:
				company_amount = own_amount + row.amount
		if fund_contribution_doc:
			if own_amount + company_amount < amount:
				frappe.throw("Own contribution is less than withdrawal amount")
			else:
				fund_contribution_doc.append("fund_contribution_entry", {
						"contribution_type": "Own",
						"amount": -amount,
						"date": self.withdrawal_date,
						"is_fund_withdrawal" : 1
					})
				fund_contribution_doc.append("fund_contribution_entry", {
						"contribution_type": "Company",
						"amount": -amount,
						"date": self.withdrawal_date,
						"is_fund_withdrawal" : 1
					})
				fund_contribution_doc.save()

