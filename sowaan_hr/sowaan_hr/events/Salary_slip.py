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

        fc_start_date = contribution_doc.start_date
        fc_start_date = frappe.utils.getdate(fc_start_date)
        

        # if fund_setting.on_confirmation == 1:
        #     confirmation_date = frappe.get_value("Employee", self.employee, "final_confirmation_date")
        #     confirmation_date = frappe.utils.getdate(confirmation_date)
        #     if start_date <= confirmation_date <= end_date:
        #         days = frappe.utils.date_diff(self.end_date, confirmation_date)+1
        #         if confirmation_date.month == 2:
        #             if days == 29 or days == 28:
        #                 days = 30
        #         elif days == 31:
        #             days = 30
        if fc_start_date:
            start_days = frappe.utils.date_diff(self.end_date, fc_start_date)+1
            
                






        if fund_setting.calculation_type == "Fixed":
            if start_days and fund_setting.own_value and fund_setting.company_value:
                    own_fund_value = (fund_setting.own_value / w_days) * start_days
                    company_fund_value = (fund_setting.company_value / w_days) * start_days
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
                
                # found_own_entry = False
                for row in contribution_doc.fund_contribution_entry:
                    if row.contribution_type == "Own" and row.salary_slip == self.name:
                        # row.amount = fund_setting.own_value  # Update the amount
                        frappe.db.set_value("Fund Contribution Entry", row.name, "amount", own_fund_value)
                        # found_own_entry = True
                        break



            if fund_setting.company_fund_component and fund_setting.company_value:
                self.earnings = [
                        row for row in self.earnings
                        if row.salary_component != fund_setting.company_fund_component
                    ]
                row2 = {"salary_component": fund_setting.company_fund_component , "amount" : company_fund_value, "year_to_date" : company_fund_value }
                self.append("earnings", row2)
                
                # found_company_entry = False
                for row in contribution_doc.fund_contribution_entry:
                    if row.contribution_type == "Company" and row.salary_slip == self.name:
                        # row.amount = fund_setting.company_value
                        frappe.db.set_value("Fund Contribution Entry", row.name, "amount", company_fund_value)
                        # found_company_entry = True
                        break
               





        
        elif fund_setting.calculation_type == "% of Payment":
            
            earnings_dict = {earning.salary_component: earning.amount for earning in self.earnings}
            if fund_setting.dependent_components:
                total_fund_amount11 = 0

                employee_arrears = frappe.get_list("Employee Arrears", filters={"employee": self.employee, "from_date":self.start_date,"to_date":self.end_date, "docstatus": 1}, fields=["*"])
                if employee_arrears:
                    employee_arrears_doc = frappe.get_doc("Employee Arrears", employee_arrears[0])
                    earnings_dict_arrears = {earning.salary_component: earning.amount for earning in employee_arrears_doc.e_a_earnings}



                for component in fund_setting.dependent_components:
                    if component.component in earnings_dict:
                        earnings_amount = 0

                        if component.component in earnings_dict:
                            earnings_amount += earnings_dict[component.component]

                        # Check if component exists in earnings_dict_arrears and add its amount
                        if employee_arrears and component.component in earnings_dict_arrears:
                            earnings_amount += earnings_dict_arrears[component.component]
                        # earnings_amount = earnings_dict[component.component]
                        calculated_amount = round((earnings_amount * component.percent) / 100, 2)
                        total_fund_amount11 = total_fund_amount11 + calculated_amount
                        
                # if start_days:
                #     total_fund_amount11 = (total_fund_amount11 / w_days) * start_days
            
                if total_fund_amount11 and fund_setting.own_value:
                            total_fund_amount11 = total_fund_amount11 * (fund_setting.own_value / 100)
                

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
                   

                    # found_own_entry = False
                    for row in contribution_doc.fund_contribution_entry:
                        if row.contribution_type == "Own" and row.salary_slip == self.name:
                            # row.amount = total_fund_amount11
                            frappe.db.set_value("Fund Contribution Entry", row.name, "amount", total_fund_amount11)
                            # found_own_entry = True
                            break




            if fund_setting.company_dependent_components:
                total_fund_amount = 0

                for component in fund_setting.company_dependent_components:
                    if component.component in earnings_dict:
                        earnings_amount = 0
                        if component.component in earnings_dict:
                            earnings_amount += earnings_dict[component.component]

                        # Check if component exists in earnings_dict_arrears and add its amount
                        if employee_arrears and component.component in earnings_dict_arrears:
                            earnings_amount += earnings_dict_arrears[component.component]
                        # earnings_amount = earnings_dict[component.component]
                        calculated_amount = round((earnings_amount * component.percent) / 100, 2)
                        total_fund_amount = total_fund_amount + calculated_amount
                # if start_days:
                #     total_fund_amount = (total_fund_amount / w_days) * start_days
                if total_fund_amount and fund_setting.company_value:
                            total_fund_amount = total_fund_amount * (fund_setting.company_value / 100)
                
                

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
                  
                    # found_company_entry = False
                    for row in contribution_doc.fund_contribution_entry:
                        if row.contribution_type == "Company" and row.salary_slip == self.name:
                            # row.amount = total_fund_amount
                            frappe.db.set_value("Fund Contribution Entry", row.name, "amount", total_fund_amount)
                            # found_company_entry = True
                            break
 
            else:
                self.earnings = [
                    row for row in self.earnings
                    if row.salary_component not in [fund_setting.company_fund_component]
                ]




        
        elif fund_setting.calculation_type == "% of Rate":

            employee_increment = frappe.get_list(
                "Employee Increment",
                filters={
                    "employee": self.employee,
                    "increment_date": ["between", [self.start_date, self.end_date]],
                    "docstatus": 1
                },
                fields=["name", "increment_date"]
            )

            if employee_increment:
                increment_date = frappe.get_value("Employee Increment", employee_increment[0].name, "increment_date")
            else:
                increment_date = None

            salary_structure = frappe.get_doc("Salary Structure", self.salary_structure)
            earnings_dict1 = {
                earning.salary_component: earning.formula
                for earning in salary_structure.get("earnings")
            }

            # Fetch base salary before increment
            previous_salary_structure_assignment = frappe.db.sql("""
                SELECT base 
                FROM `tabSalary Structure Assignment`
                WHERE salary_structure = %s
                AND from_date < %s
                AND employee = %s
                AND docstatus = 1
                ORDER BY from_date DESC
                LIMIT 1
            """, (self.salary_structure, increment_date if increment_date else self.start_date, self.employee), as_dict=True)
            
            previous_base_value = previous_salary_structure_assignment[0].base if previous_salary_structure_assignment else 0

            # Fetch base salary after increment
            latest_salary_structure_assignment = frappe.db.sql("""
                SELECT base 
                FROM `tabSalary Structure Assignment`
                WHERE salary_structure = %s
                AND from_date <= %s
                AND employee = %s
                AND docstatus = 1
                ORDER BY from_date DESC
                LIMIT 1
            """, (self.salary_structure, self.end_date, self.employee), as_dict=True)
            
            latest_base_value = latest_salary_structure_assignment[0].base if latest_salary_structure_assignment else previous_base_value

            total_fund_amount1 = 0

            if fund_setting.dependent_components:
                # Part 1: Calculation before increment date
                if increment_date:
                    days_before_increment = frappe.utils.date_diff(increment_date, self.start_date)
                    for component in fund_setting.dependent_components:
                        if component.component in earnings_dict1:
                            formula = earnings_dict1[component.component]
                            
                            earnings_amount = frappe.safe_eval(formula, {}, {"custom_base": previous_base_value})
                            
                            calculated_amount = round((earnings_amount * component.percent) / 100, 2)
                            total_fund_amount1 += (calculated_amount / w_days) * days_before_increment
                            

                # Part 2: Calculation after increment date
                days_after_increment = frappe.utils.date_diff(self.end_date, increment_date)+1 if increment_date else w_days
                for component in fund_setting.dependent_components:
                    if component.component in earnings_dict1:
                        formula = earnings_dict1[component.component]
                       
                        earnings_amount = frappe.safe_eval(formula, {}, {"custom_base": latest_base_value})
                        
                        calculated_amount = round((earnings_amount * component.percent) / 100, 2)
                        total_fund_amount1 += (calculated_amount / w_days) * days_after_increment
                        
            if total_fund_amount1 and fund_setting.own_value:
                                total_fund_amount1 = total_fund_amount1 * (fund_setting.own_value / 100)

            # Deduction logic remains the same
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

                # Update Fund Contribution Entry
                for row in contribution_doc.fund_contribution_entry:
                    if row.contribution_type == "Own" and row.salary_slip == self.name:
                        frappe.db.set_value("Fund Contribution Entry", row.name, "amount", total_fund_amount1)
                        break



            total_fund_amount2 = 0

            if fund_setting.company_dependent_components:
                # Part 1: Calculation before increment date
                if increment_date:
                    days_before_increment = frappe.utils.date_diff(increment_date, self.start_date)
                    for component in fund_setting.company_dependent_components:
                        if component.component in earnings_dict1:
                            formula = earnings_dict1[component.component]
                            earnings_amount = frappe.safe_eval(formula, {}, {"custom_base": previous_base_value})
                            calculated_amount = round((earnings_amount * component.percent) / 100, 2)
                            total_fund_amount2 += (calculated_amount / w_days) * days_before_increment
                            
                # Part 2: Calculation after increment date
                days_after_increment = frappe.utils.date_diff(self.end_date, increment_date) + 1 if increment_date else w_days
                for component in fund_setting.company_dependent_components:
                    if component.component in earnings_dict1:
                        formula = earnings_dict1[component.component]
                        earnings_amount = frappe.safe_eval(formula, {}, {"custom_base": latest_base_value})
                        calculated_amount = round((earnings_amount * component.percent) / 100, 2)
                        total_fund_amount2 += (calculated_amount / w_days) * days_after_increment
                        
                if total_fund_amount2 and fund_setting.company_value:
                            total_fund_amount2 = total_fund_amount2 * (fund_setting.company_value / 100)


                # Removing previous earnings entry
                self.earnings = [
                    row for row in self.earnings
                    if row.salary_component not in [fund_setting.company_fund_component]
                ]

                # Adding new earnings entry
                if total_fund_amount2 > 0:
                    self.append("earnings", {
                        "salary_component": fund_setting.company_fund_component,
                        "amount": total_fund_amount2,
                        "year_to_date": total_fund_amount2
                    })

                    # Updating Fund Contribution Entry
                    for row in contribution_doc.fund_contribution_entry:
                        if row.contribution_type == "Company" and row.salary_slip == self.name:
                            frappe.db.set_value("Fund Contribution Entry", row.name, "amount", total_fund_amount2)
                            break

   
    self.custom_check_adjustment = 0
    self.calculate_net_pay()
    self.compute_year_to_date()
    self.compute_month_to_date()
    self.compute_component_wise_year_to_date()
    set_fix_days(self)




def salary_slip_after_submit(self,method):
    
    fund_contribution = frappe.get_list(
            "Fund Contribution",
            filters={
                "employee": self.employee,
                "docstatus": 1
            },
            fields=["*"],
            
        )
    if fund_contribution:
        own_fund_value = 0
        company_fund_value = 0
        contribution_doc = frappe.get_doc("Fund Contribution", fund_contribution[0])
        fund_setting_name = contribution_doc.fund_setting
        fund_setting = frappe.get_doc("Fund Setting", fund_setting_name)
        own_component_name = fund_setting.fund_component
        company_component_name = fund_setting.company_fund_component

        for row in self.deductions:
            if row.salary_component == own_component_name:
                own_fund_value = row.amount
                break
        for row in self.earnings:
            if row.salary_component == company_component_name:
                company_fund_value = row.amount
                break



        found_own_entry = False
        for row in contribution_doc.fund_contribution_entry:
            if row.contribution_type == "Own" and row.reference_doctype == "Salary Slip" and row.document_name == self.name:
                # row.amount = fund_setting.own_value  # Update the amount
                frappe.db.set_value("Fund Contribution Entry", row.name, "amount", own_fund_value)
                found_own_entry = True
                break


        if not found_own_entry:

            contribution_doc.append("fund_contribution_entry", {
                "contribution_type": "Own",
                "amount": own_fund_value,
                "date": self.posting_date,
                "reference_doctype": "Salary Slip",
                "document_name":self.name
            })
            contribution_doc.save()



        found_company_entry = False
        for row in contribution_doc.fund_contribution_entry:
            if row.contribution_type == "Company" and row.reference_doctype == "Salary Slip" and row.document_name == self.name:
                frappe.db.set_value("Fund Contribution Entry", row.name, "amount", company_fund_value)
                found_company_entry = True
                break
        if not found_company_entry:
            contribution_doc.append("fund_contribution_entry", {
                "contribution_type": "Company",
                "amount": company_fund_value,
                "date": self.posting_date,
                "reference_doctype": "Salary Slip",
                "document_name":self.name
            })
            contribution_doc.save()



def set_fix_days(self):
    calculation_criteria = frappe.db.get_single_value('Sowaan HR Settings', 'calculation_criteria')
    if calculation_criteria == "Fix Days":
        self.total_working_days = int(frappe.db.get_single_value('Sowaan HR Settings', 'days'))
        

        



def cancel_related_docs(self, method):
    fund_contribution = frappe.get_list("Fund Contribution", filters={"employee": self.employee,"docstatus": 1})
    
    if fund_contribution:
        fund_contribution_doc = frappe.get_doc("Fund Contribution", fund_contribution[0].name)

        if fund_contribution_doc:
            for i in range(len(fund_contribution_doc.fund_contribution_entry) - 1, -1, -1):
                row = fund_contribution_doc.fund_contribution_entry[i]
                if row.reference_doctype == "Salary Slip" and str(row.document_name) == str(self.name):
                    print("Working in Condition")
                    del fund_contribution_doc.fund_contribution_entry[i]

            fund_contribution_doc.save()
        







