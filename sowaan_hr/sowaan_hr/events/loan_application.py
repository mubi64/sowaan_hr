import frappe
def loan_withdrawal(self, method):
    if self.loan_product and self.applicant:
        own_allowed = 0
        company_allowed = 0
        total_own_fund = 0
        applied_own = 0
        total_company_fund = 0
        applied_company = 0
        fund_contribution = frappe.get_list("Fund Contribution", filters={"employee":self.applicant,"docstatus":1} )
        fund_contribution_doc = None
        fund_setting = None

        active = 0
        if fund_contribution:
            fund_contribution_doc = frappe.get_doc("Fund Contribution" , fund_contribution[0].name)
        if fund_contribution_doc:
            fund_setting = frappe.get_doc("Fund Setting",fund_contribution_doc.fund_setting)
        if fund_setting:
            for row in fund_setting.fund_setting_loan_product:
                if row.loan_product == self.loan_product and row.active == 1:
                    active = 1
                    own_allowed = row.allowed__of_own_contribution
                    company_allowed = row.allowed__of_company_contribution
                    break
        if active:
            if own_allowed:
                for row in fund_contribution_doc.fund_contribution_entry:
                    if row.contribution_type == "Own":
                            total_own_fund = total_own_fund + row.amount
                applied_own = (total_own_fund * own_allowed ) / 100
            if company_allowed:
                for row in fund_contribution_doc.fund_contribution_entry:
                        if row.contribution_type == "Company":
                            total_company_fund = total_company_fund + row.amount
                applied_company = (total_company_fund * company_allowed ) / 100
            if self.loan_amount > (applied_own + applied_company):
                    frappe.throw("Loan amount can not exceed allowed percentage")


    # if self.loan_product and self.loan_amount:    
        # fund_setting_name = frappe.get_all(
        #     "Fund Setting Loan Product",
        #     filters={"loan_product": self.loan_product},
        #     fields=["parent"]
        # )
       

        # if fund_setting_name:
        #     fund_setting_own_allowed = frappe.get_value("Fund Setting",fund_setting_name[0].parent, "allowed__of_own_contribution")
        #     fund_setting_company_allowed = frappe.get_value("Fund Setting",fund_setting_name[0].parent, "allowed__of_company_contribution")
        #     fund_contribution_name = frappe.get_list("Fund Contribution", filters={"fund_setting": fund_setting_name[0].parent , "employee": self.applicant, "start_date": ["<=", self.posting_date],"docstatus": 1})
        #     fund_contribution = frappe.get_doc("Fund Contribution",fund_contribution_name[0].name )
        #     total_own_fund = 0
        #     total_company_fund = 0
        #     applied_own= 0
        #     applied_company = 0
        #     if fund_setting_own_allowed:
        #         for i in fund_contribution.fund_contribution_entry:
        #             if i.contribution_type == "Own":
        #                 total_own_fund = total_own_fund + i.amount
        #         applied_own = (total_own_fund * fund_setting_own_allowed ) / 100

        #     if fund_setting_company_allowed:
        #         for i in fund_contribution.fund_contribution_entry:
        #             if i.contribution_type == "Company":
        #                 total_company_fund = total_company_fund + i.amount
        #         applied_company = (total_company_fund * fund_setting_company_allowed ) / 100

        #     if self.loan_amount > (applied_own + applied_company):
        #         frappe.throw("Loan amount can not exceed allowed percentage")
