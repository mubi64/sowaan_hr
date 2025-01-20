import frappe
from hrms.payroll.doctype.salary_slip.salary_slip import (SalarySlip, calculate_tax_by_tax_slab)
from sowaan_hr.sowaan_hr.api.api import create_salary_adjustment_for_negative_salary


def fund_management_and_negative_salary(self, method):
    if self.custom_adjust_negative_salary == 1 and self.custom_check_adjustment == 1 and self.net_pay < 0 :
            create_salary_adjustment_for_negative_salary(self.name)
        
    elif self.net_pay < 0 :
        self.custom_adjust_negative_salary = 0

    fund_contribution = frappe.get_list(
            "Fund Contribution",
            filters={
                "employee": self.employee,
                "docstatus": 1
            },
            fields=["*"],
            
        )
    if fund_contribution:
        contribution_doc = frappe.get_doc("Fund Contribution", fund_contribution[0])
        fund_setting_name = contribution_doc.fund_setting
        fund_setting = frappe.get_doc("Fund Setting", fund_setting_name)






        if fund_setting.calculation_type == "Fixed":

            if fund_setting.fund_component and fund_setting.own_value:
                self.deductions = [
                        row for row in self.deductions
                        if row.salary_component != fund_setting.fund_component
                    ]
                row1 = {"salary_component": fund_setting.fund_component , "amount" : fund_setting.own_value, "year_to_date" : fund_setting.own_value }
                self.append("deductions", row1)
                
                found_own_entry = False
                for row in contribution_doc.fund_contribution_entry:
                    if row.contribution_type == "Own" and row.salary_slip == self.name:
                        # row.amount = fund_setting.own_value  # Update the amount
                        frappe.db.set_value("Fund Contribution Entry", row.name, "amount", fund_setting.own_value)
                        found_own_entry = True
                        break


                if not found_own_entry:

                    contribution_doc.append("fund_contribution_entry", {
                        "contribution_type": "Own",
                        "amount": fund_setting.own_value,
                        "date": self.posting_date,
                        "salary_slip": self.name
                    })
                    contribution_doc.save()


            if fund_setting.company_fund_component and fund_setting.company_value:
                self.earnings = [
                        row for row in self.earnings
                        if row.salary_component != fund_setting.company_fund_component
                    ]
                row2 = {"salary_component": fund_setting.company_fund_component , "amount" : fund_setting.company_value, "year_to_date" : fund_setting.company_value }
                self.append("earnings", row2)
                
                found_company_entry = False
                for row in contribution_doc.fund_contribution_entry:
                    if row.contribution_type == "Company" and row.salary_slip == self.name:
                        # row.amount = fund_setting.company_value
                        frappe.db.set_value("Fund Contribution Entry", row.name, "amount", fund_setting.company_value)
                        found_company_entry = True
                        break
                if not found_company_entry:
                    contribution_doc.append("fund_contribution_entry", {
                        "contribution_type": "Company",
                        "amount": fund_setting.company_value,
                        "date": self.posting_date,
                        "salary_slip": self.name
                    })
                    contribution_doc.save()





        
        elif fund_setting.calculation_type == "% of Payment":

            earnings_dict = {earning.salary_component: earning.amount for earning in self.earnings}
            if fund_setting.dependent_components:
                total_fund_amount11 = 0

                for component in fund_setting.dependent_components:
                    if component.component in earnings_dict:
                        earnings_amount = earnings_dict[component.component]
                        calculated_amount = round((earnings_amount * component.percent) / 100, 2)
                        total_fund_amount11 = total_fund_amount11 + calculated_amount

                self.deductions = [
                    row for row in self.deductions
                    if row.salary_component not in [fund_setting.fund_component]
                ]

                if total_fund_amount11 > 0:
                    self.append("deductions", {
                        "salary_component": fund_setting.fund_component,
                        "amount": total_fund_amount11,
                        "year_to_date": total_fund_amount11
                    })
                   

                    found_own_entry = False
                    for row in contribution_doc.fund_contribution_entry:
                        if row.contribution_type == "Own" and row.salary_slip == self.name:
                            # row.amount = total_fund_amount11
                            frappe.db.set_value("Fund Contribution Entry", row.name, "amount", total_fund_amount11)
                            found_own_entry = True
                            break


                    if not found_own_entry:
                        # contribution_doc.fund_contribution_entry = []
                        contribution_doc.append("fund_contribution_entry", {
                            "contribution_type": "Own",
                            "amount": total_fund_amount11,
                            "date": self.posting_date,
                            "salary_slip": self.name
                        })
                        contribution_doc.save()



            if fund_setting.company_dependent_components:
                total_fund_amount = 0

                for component in fund_setting.company_dependent_components:
                    if component.component in earnings_dict:
                        earnings_amount = earnings_dict[component.component]
                        calculated_amount = round((earnings_amount * component.percent) / 100, 2)
                        total_fund_amount = total_fund_amount + calculated_amount

                self.earnings = [
                    row for row in self.earnings
                    if row.salary_component not in [fund_setting.company_fund_component]
                ]

                if total_fund_amount > 0:
                    self.append("earnings", {
                        "salary_component": fund_setting.company_fund_component,
                        "amount": total_fund_amount,
                        "year_to_date": total_fund_amount
                    })
                  
                    found_company_entry = False
                    for row in contribution_doc.fund_contribution_entry:
                        if row.contribution_type == "Company" and row.salary_slip == self.name:
                            # row.amount = total_fund_amount
                            frappe.db.set_value("Fund Contribution Entry", row.name, "amount", total_fund_amount)
                            found_company_entry = True
                            break
                    if not found_company_entry:
                        # contribution_doc.fund_contribution_entry = []
                        contribution_doc.append("fund_contribution_entry", {
                            "contribution_type": "Company",
                            "amount": total_fund_amount,
                            "date": self.posting_date,
                            "salary_slip": self.name
                        })
                        contribution_doc.save()



            else:
                self.earnings = [
                    row for row in self.earnings
                    if row.salary_component not in [fund_setting.company_fund_component]
                ]




        elif fund_setting.calculation_type == "% of Rate":
            salary_structure = frappe.get_doc("Salary Structure", self.salary_structure)
            earnings_dict1 = {
                earning.salary_component: earning.formula
                for earning in salary_structure.get("earnings")
            }
            salary_structure_assignment = frappe.db.sql("""
                SELECT base 
                FROM `tabSalary Structure Assignment`
                WHERE salary_structure = %s
                AND from_date BETWEEN %s AND %s
                ORDER BY from_date DESC
                LIMIT 1
            """, (self.salary_structure, self.start_date, self.end_date), as_dict=True)
            base_value = salary_structure_assignment[0].base if salary_structure_assignment else 0
            total_fund_amount1 = 0

            if fund_setting.dependent_components:
                for component in fund_setting.dependent_components:
                    
                    if component.component in earnings_dict1:
                        formula = earnings_dict1[component.component]
                        earnings_amount = frappe.safe_eval(formula, {}, {"custom_base": base_value})
                        calculated_amount = round((earnings_amount * component.percent) / 100, 2)
                        total_fund_amount1 = total_fund_amount1 + calculated_amount
                self.deductions = [
                    row for row in self.deductions
                    if row.salary_component not in [fund_setting.fund_component]
                ]   
                if total_fund_amount1 > 0:
                    self.append("deductions", {
                        "salary_component": fund_setting.fund_component,
                        "amount": total_fund_amount1,
                        "year_to_date": total_fund_amount1
                    })
        
                    found_own_entry = False
                    for row in contribution_doc.fund_contribution_entry:
                        if row.contribution_type == "Own" and row.salary_slip == self.name:
                            # row.amount = total_fund_amount1
                            frappe.db.set_value("Fund Contribution Entry", row.name, "amount", total_fund_amount1)
                            found_own_entry = True
                            break
                    if not found_own_entry:
                        contribution_doc.append("fund_contribution_entry", {
                            "contribution_type": "Own",
                            "amount": total_fund_amount1,
                            "date": self.posting_date,
                            "salary_slip": self.name
                        })
                        contribution_doc.save()






            total_fund_amount2 = 0
            if fund_setting.company_dependent_components:
                for component in fund_setting.company_dependent_components:
                    
                    if component.component in earnings_dict1:
                        formula = earnings_dict1[component.component]
                        earnings_amount = frappe.safe_eval(formula, {}, {"custom_base": base_value})
                        calculated_amount = round((earnings_amount * component.percent) / 100, 2)
                        total_fund_amount2 = total_fund_amount2 + calculated_amount
                self.earnings = [
                    row for row in self.earnings
                    if row.salary_component not in [fund_setting.company_fund_component]
                ]
                if total_fund_amount2 > 0:
                    self.append("earnings", {
                        "salary_component": fund_setting.company_fund_component,
                        "amount": total_fund_amount2,
                        "year_to_date": total_fund_amount2
                    })
        
                    found_company_entry = False
                    for row in contribution_doc.fund_contribution_entry:
                        if row.contribution_type == "Company" and row.salary_slip == self.name:
                            # row.amount = total_fund_amount2
                            frappe.db.set_value("Fund Contribution Entry", row.name, "amount", total_fund_amount2)
                            found_company_entry = True
                            break
                    if not found_company_entry:
                        contribution_doc.append("fund_contribution_entry", {
                            "contribution_type": "Company",
                            "amount": total_fund_amount2,
                            "date": self.posting_date,
                            "salary_slip": self.name
                        })
                        contribution_doc.save()
        
    else:
        frappe.msgprint("Fund Contribution not found for this employee")

    self.custom_check_adjustment = 0
    self.calculate_net_pay()
    self.compute_year_to_date()
    self.compute_month_to_date()
    self.compute_component_wise_year_to_date()


def loan_withdrawal(self, method):
    if self.loan_product and self.loan_amount:
        fund_setting_name = frappe.get_list("Fund Setting" , filters = {"loan":self.loan_product,
        "docstatus": 1})
        fund_setting_loan = frappe.get_value("Fund Setting",fund_setting_name[0].name, "loan")
        fund_setting_own_allowed = frappe.get_value("Fund Setting",fund_setting_name[0].name, "allowed__of_own_contribution")
        fund_setting_company_allowed = frappe.get_value("Fund Setting",fund_setting_name[0].name, "allowed__of_company_contribution")
        fund_contribution_name = frappe.get_list("Fund Contribution", filters={"fund_setting": fund_setting_name[0].name , "employee": self.applicant, "start_date": ["<=", self.posting_date],"docstatus": 1})
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

        


