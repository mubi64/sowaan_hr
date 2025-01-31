import frappe
def loan_withdrawal(self, method):
    if self.loan_product and self.loan_amount:
        # fund_setting_name = frappe.get_list("Fund Setting" , filters = {"loan":self.loan_product,
        # "docstatus": 1})
        fund_setting_name = frappe.get_all(
            "Fund Setting Loan Product",
            filters={"loan_product": self.loan_product},
            fields=["parent"]
        )
        # if not fund_setting_name:
        #     frappe.msgprint("No Fund Setting found for this loan product")

        if fund_setting_name:
            # fund_setting_loan = frappe.get_value("Fund Setting",fund_setting_name[0].parent, "loan")
            fund_setting_own_allowed = frappe.get_value("Fund Setting",fund_setting_name[0].parent, "allowed__of_own_contribution")
            fund_setting_company_allowed = frappe.get_value("Fund Setting",fund_setting_name[0].parent, "allowed__of_company_contribution")
            fund_contribution_name = frappe.get_list("Fund Contribution", filters={"fund_setting": fund_setting_name[0].parent , "employee": self.applicant, "start_date": ["<=", self.posting_date],"docstatus": 1})
            fund_contribution = frappe.get_doc("Fund Contribution",fund_contribution_name[0].name )
            total_own_fund = 0
            total_company_fund = 0
            applied_own= 0
            applied_company = 0
            if fund_setting_own_allowed:
                for i in fund_contribution.fund_contribution_entry:
                    if i.contribution_type == "Own":
                        total_own_fund = total_own_fund + i.amount
                applied_own = (total_own_fund * fund_setting_own_allowed ) / 100

            if fund_setting_company_allowed:
                for i in fund_contribution.fund_contribution_entry:
                    if i.contribution_type == "Company":
                        total_company_fund = total_company_fund + i.amount
                applied_company = (total_company_fund * fund_setting_company_allowed ) / 100

            if self.loan_amount > (applied_own + applied_company):
                frappe.throw("Loan amount can not exceed allowed percentage")