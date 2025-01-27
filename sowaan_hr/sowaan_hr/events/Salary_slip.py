import frappe
from hrms.payroll.doctype.salary_slip.salary_slip import (SalarySlip, calculate_tax_by_tax_slab)
from sowaan_hr.sowaan_hr.api.api import create_salary_adjustment_for_negative_salary
from datetime import datetime


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
        days = 0
        w_days = 0
        contribution_doc = frappe.get_doc("Fund Contribution", fund_contribution[0])
        fund_setting_name = contribution_doc.fund_setting
        fund_setting = frappe.get_doc("Fund Setting", fund_setting_name)
        if fund_setting.calculation_method == "Fixed Days":
            w_days = fund_setting.days
        elif fund_setting.calculation_method == "Working Days":
            w_days = self.total_working_days
        start_date = frappe.utils.getdate(self.start_date)
        end_date = frappe.utils.getdate(self.end_date)
        if fund_setting.on_confirmation == 1:
            confirmation_date = frappe.get_value("Employee", self.employee, "final_confirmation_date")
            confirmation_date = frappe.utils.getdate(confirmation_date)
            if start_date <= confirmation_date <= end_date:
                days = frappe.utils.date_diff(self.end_date, confirmation_date)+1
                if confirmation_date.month == 2:
                    if days == 29 or days == 28:
                        days = 30
                elif days == 31:
                    days = 30
                






        if fund_setting.calculation_type == "Fixed":
            if days and fund_setting.own_value and fund_setting.company_value:
                    own_fund_value = (fund_setting.own_value / w_days) * days
                    company_fund_value = (fund_setting.company_value / w_days) * days
            else:
                own_fund_value = fund_setting.own_value
                company_fund_value = fund_setting.company_value

            if fund_setting.fund_component and fund_setting.own_value:
                self.deductions = [
                        row for row in self.deductions
                        if row.salary_component != fund_setting.fund_component
                    ]
                
                row1 = {"salary_component": fund_setting.fund_component , "amount" : own_fund_value, "year_to_date" : own_fund_value }
                self.append("deductions", row1)
                
                found_own_entry = False
                for row in contribution_doc.fund_contribution_entry:
                    if row.contribution_type == "Own" and row.salary_slip == self.name:
                        # row.amount = fund_setting.own_value  # Update the amount
                        frappe.db.set_value("Fund Contribution Entry", row.name, "amount", own_fund_value)
                        found_own_entry = True
                        break


                if not found_own_entry:

                    contribution_doc.append("fund_contribution_entry", {
                        "contribution_type": "Own",
                        "amount": own_fund_value,
                        "date": self.posting_date,
                        "salary_slip": self.name
                    })
                    contribution_doc.save()


            if fund_setting.company_fund_component and fund_setting.company_value:
                self.earnings = [
                        row for row in self.earnings
                        if row.salary_component != fund_setting.company_fund_component
                    ]
                row2 = {"salary_component": fund_setting.company_fund_component , "amount" : company_fund_value, "year_to_date" : company_fund_value }
                self.append("earnings", row2)
                
                found_company_entry = False
                for row in contribution_doc.fund_contribution_entry:
                    if row.contribution_type == "Company" and row.salary_slip == self.name:
                        # row.amount = fund_setting.company_value
                        frappe.db.set_value("Fund Contribution Entry", row.name, "amount", company_fund_value)
                        found_company_entry = True
                        break
                if not found_company_entry:
                    contribution_doc.append("fund_contribution_entry", {
                        "contribution_type": "Company",
                        "amount": company_fund_value,
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
                if days:
                    total_fund_amount11 = (total_fund_amount11 / w_days) * days

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
                if days:
                    total_fund_amount = (total_fund_amount / w_days) * days

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
                AND from_date <= %s
                AND employee = %s
                ORDER BY from_date DESC
                LIMIT 1
            """, (self.salary_structure, self.end_date, self.employee), as_dict=True)
            base_value = salary_structure_assignment[0].base if salary_structure_assignment else 0
            total_fund_amount1 = 0

            if fund_setting.dependent_components:
                for component in fund_setting.dependent_components:
                    
                    if component.component in earnings_dict1:
                        formula = earnings_dict1[component.component]
                        earnings_amount = frappe.safe_eval(formula, {}, {"custom_base": base_value})
                        
                        calculated_amount = round((earnings_amount * component.percent) / 100, 2)
                        total_fund_amount1 = total_fund_amount1 + calculated_amount
                        
                if days:
                    total_fund_amount1 = (total_fund_amount1 / w_days) * days
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
                if days:
                    total_fund_amount2 = (total_fund_amount2 / w_days) * days
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
        
    
    self.custom_check_adjustment = 0
    self.calculate_net_pay()
    self.compute_year_to_date()
    self.compute_month_to_date()
    self.compute_component_wise_year_to_date()




        


