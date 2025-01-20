# Copyright (c) 2024, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class FundContribution(Document):
    def before_submit(self):
        if self.opening_own_balance:
            self.append("fund_contribution_entry", {
                "contribution_type": "Own",
                "amount": self.opening_own_balance,
                "date": self.start_date,
                "is_opening_balance": 1
            })

        if self.opening_company_balance:
            self.append("fund_contribution_entry", {
                "contribution_type": "Company",
                "amount": self.opening_company_balance,
                "date": self.start_date,
                "is_opening_balance": 1
            })

        # Save once after all modifications
        # self.save()