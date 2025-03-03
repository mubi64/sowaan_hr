import frappe
from hrms.payroll.doctype.salary_slip.salary_slip import (SalarySlip, calculate_tax_by_tax_slab)
from sowaan_hr.sowaan_hr.api.api import create_salary_adjustment_for_negative_salary
from datetime import datetime, timedelta


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
                
                # row1 = {"salary_component": fund_setting.fund_component , "amount" : own_fund_value, "year_to_date" : own_fund_value }
                # self.append("deductions", row1)
                own_component = frappe.get_doc("Salary Component",fund_setting.fund_component)
                own_statistical_component = own_component.depends_on_payment_days
                own_is_taxable = own_component.is_tax_applicable
                own_is_felexible_benifit = own_component.is_flexible_benefit
                own_d_include_in_total = own_component.do_not_include_in_total
                own_d_full_tax = own_component.deduct_full_tax_on_selected_payroll_date
                own_ex_from_income_tax = own_component.exempted_from_income_tax
                own_stastical_component = own_component.statistical_component
                # Construct the dictionary for the deduction
                deduction_entry = {
                    "salary_component": fund_setting.fund_component,
                    "amount": own_fund_value,
                    "year_to_date": own_fund_value
                }

                # Add the additional properties if they exist (i.e., are not None or empty)
                if own_statistical_component is not None:
                    deduction_entry["depends_on_payment_days"] = own_statistical_component

                if own_is_taxable is not None:
                    deduction_entry["is_tax_applicable"] = own_is_taxable

                if own_is_felexible_benifit is not None:
                    deduction_entry["is_flexible_benefit"] = own_is_felexible_benifit

                if own_d_include_in_total is not None:
                    deduction_entry["do_not_include_in_total"] = own_d_include_in_total

                if own_d_full_tax is not None:
                    deduction_entry["deduct_full_tax_on_selected_payroll_date"] = own_d_full_tax
                
                if own_ex_from_income_tax is not None:
                    deduction_entry["exempted_from_income_tax"] = own_ex_from_income_tax

                if own_stastical_component is not None:
                        deduction_entry["statistical_component"] = own_stastical_component
                        

                # Append the deduction entry to the list
                self.append("deductions", deduction_entry)
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
                company_component = frappe.get_doc("Salary Component",fund_setting.company_fund_component)
                company_statistical_component = company_component.depends_on_payment_days
                company_is_taxable = company_component.is_tax_applicable
                company_is_felexible_benifit = company_component.is_flexible_benefit
                company_d_include_in_total = company_component.do_not_include_in_total
                company_d_full_tax = company_component.deduct_full_tax_on_selected_payroll_date
                company_ex_from_income_tax = company_component.exempted_from_income_tax
                company_stastical_component = company_component.statistical_component
                # row2 = {"salary_component": fund_setting.company_fund_component , "amount" : company_fund_value, "year_to_date" : company_fund_value }
                # self.append("earnings", row2)
                earningg_entry = {
                        "salary_component": fund_setting.company_fund_component,
                        "amount": company_fund_value,
                        "year_to_date": company_fund_value
                    }

                # Add the additional properties if they exist (i.e., are not None or empty)
                if company_statistical_component is not None:
                    earningg_entry["depends_on_payment_days"] = company_statistical_component

                if company_is_taxable is not None:
                    earningg_entry["is_tax_applicable"] = company_is_taxable

                if company_is_felexible_benifit is not None:
                    earningg_entry["is_flexible_benefit"] = company_is_felexible_benifit

                if company_d_include_in_total is not None:
                    earningg_entry["do_not_include_in_total"] = company_d_include_in_total

                if company_d_full_tax is not None:
                    earningg_entry["deduct_full_tax_on_selected_payroll_date"] = company_d_full_tax
                
                if company_ex_from_income_tax is not None:
                    earningg_entry["exempted_from_income_tax"] = company_ex_from_income_tax

                if company_stastical_component is not None:
                        earningg_entry["statistical_component"] = company_stastical_component
                self.append("earnings", earningg_entry)
             

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
                own_component = frappe.get_doc("Salary Component",fund_setting.fund_component)
                own_statistical_component = own_component.depends_on_payment_days
                own_is_taxable = own_component.is_tax_applicable
                own_is_felexible_benifit = own_component.is_flexible_benefit
                own_d_include_in_total = own_component.do_not_include_in_total
                own_d_full_tax = own_component.deduct_full_tax_on_selected_payroll_date
                own_ex_from_income_tax = own_component.exempted_from_income_tax
                own_stastical_component = own_component.statistical_component

                if total_fund_amount11 > 0:
                    # Construct the dictionary for the deduction
                    deduction_entry = {
                        "salary_component": fund_setting.fund_component,
                        "amount": total_fund_amount11,
                        "year_to_date": total_fund_amount11
                    }

                    # Add the additional properties if they exist (i.e., are not None or empty)
                    if own_statistical_component is not None:
                        deduction_entry["depends_on_payment_days"] = own_statistical_component

                    if own_is_taxable is not None:
                        deduction_entry["is_tax_applicable"] = own_is_taxable

                    if own_is_felexible_benifit is not None:
                        deduction_entry["is_flexible_benefit"] = own_is_felexible_benifit

                    if own_d_include_in_total is not None:
                        deduction_entry["do_not_include_in_total"] = own_d_include_in_total

                    if own_d_full_tax is not None:
                        deduction_entry["deduct_full_tax_on_selected_payroll_date"] = own_d_full_tax
                    
                    if own_ex_from_income_tax is not None:
                        deduction_entry["exempted_from_income_tax"] = own_ex_from_income_tax

                    if own_stastical_component is not None:
                         deduction_entry["statistical_component"] = own_stastical_component
                         

                    # Append the deduction entry to the list
                    self.append("deductions", deduction_entry)
                                

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

                company_component = frappe.get_doc("Salary Component",fund_setting.company_fund_component)
                company_statistical_component = company_component.depends_on_payment_days
                company_is_taxable = company_component.is_tax_applicable
                company_is_felexible_benifit = company_component.is_flexible_benefit
                company_d_include_in_total = company_component.do_not_include_in_total
                company_d_full_tax = company_component.deduct_full_tax_on_selected_payroll_date
                company_ex_from_income_tax = company_component.exempted_from_income_tax
                company_stastical_component = company_component.statistical_component


                if total_fund_amount > 0:
                    # self.append("earnings", {
                    #     "salary_component": fund_setting.company_fund_component,
                    #     "amount": total_fund_amount,
                    #     "year_to_date": total_fund_amount
                    # })

                    # Construct the dictionary for the deduction
                    earningg_entry = {
                        "salary_component": fund_setting.company_fund_component,
                        "amount": total_fund_amount,
                        "year_to_date": total_fund_amount
                    }

                    # Add the additional properties if they exist (i.e., are not None or empty)
                    if company_statistical_component is not None:
                        earningg_entry["depends_on_payment_days"] = company_statistical_component

                    if company_is_taxable is not None:
                        earningg_entry["is_tax_applicable"] = company_is_taxable

                    if company_is_felexible_benifit is not None:
                        earningg_entry["is_flexible_benefit"] = company_is_felexible_benifit

                    if company_d_include_in_total is not None:
                        earningg_entry["do_not_include_in_total"] = company_d_include_in_total

                    if company_d_full_tax is not None:
                        earningg_entry["deduct_full_tax_on_selected_payroll_date"] = company_d_full_tax
                    
                    if company_ex_from_income_tax is not None:
                        earningg_entry["exempted_from_income_tax"] = company_ex_from_income_tax

                    if company_stastical_component is not None:
                         earningg_entry["statistical_component"] = company_stastical_component
                         

                    # Append the deduction entry to the list
                    self.append("earnings", earningg_entry)



                  
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
                
                own_component = frappe.get_doc("Salary Component",fund_setting.fund_component)
                own_statistical_component = own_component.depends_on_payment_days
                own_is_taxable = own_component.is_tax_applicable
                own_is_felexible_benifit = own_component.is_flexible_benefit
                own_d_include_in_total = own_component.do_not_include_in_total
                own_d_full_tax = own_component.deduct_full_tax_on_selected_payroll_date
                own_ex_from_income_tax = own_component.exempted_from_income_tax
                own_stastical_component = own_component.statistical_component

            
                # Construct the dictionary for the deduction
                deduction_entry = {
                    "salary_component": fund_setting.fund_component,
                    "amount": total_fund_amount1,
                    "year_to_date": total_fund_amount1
                }

                # Add the additional properties if they exist (i.e., are not None or empty)
                if own_statistical_component is not None:
                    deduction_entry["depends_on_payment_days"] = own_statistical_component

                if own_is_taxable is not None:
                    deduction_entry["is_tax_applicable"] = own_is_taxable

                if own_is_felexible_benifit is not None:
                    deduction_entry["is_flexible_benefit"] = own_is_felexible_benifit

                if own_d_include_in_total is not None:
                    deduction_entry["do_not_include_in_total"] = own_d_include_in_total

                if own_d_full_tax is not None:
                    deduction_entry["deduct_full_tax_on_selected_payroll_date"] = own_d_full_tax
                
                if own_ex_from_income_tax is not None:
                    deduction_entry["exempted_from_income_tax"] = own_ex_from_income_tax

                if own_stastical_component is not None:
                        deduction_entry["statistical_component"] = own_stastical_component
                        

                # Append the deduction entry to the list
                self.append("deductions", deduction_entry)

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
                company_component = frappe.get_doc("Salary Component",fund_setting.company_fund_component)
                company_statistical_component = company_component.depends_on_payment_days
                company_is_taxable = company_component.is_tax_applicable
                company_is_felexible_benifit = company_component.is_flexible_benefit
                company_d_include_in_total = company_component.do_not_include_in_total
                company_d_full_tax = company_component.deduct_full_tax_on_selected_payroll_date
                company_ex_from_income_tax = company_component.exempted_from_income_tax
                company_stastical_component = company_component.statistical_component


                if total_fund_amount2 > 0:
                    # Construct the dictionary for the deduction
                    earningg_entry = {
                        "salary_component": fund_setting.company_fund_component,
                        "amount": total_fund_amount2,
                        "year_to_date": total_fund_amount2
                    }

                    # Add the additional properties if they exist (i.e., are not None or empty)
                    if company_statistical_component is not None:
                        earningg_entry["depends_on_payment_days"] = company_statistical_component

                    if company_is_taxable is not None:
                        earningg_entry["is_tax_applicable"] = company_is_taxable

                    if company_is_felexible_benifit is not None:
                        earningg_entry["is_flexible_benefit"] = company_is_felexible_benifit

                    if company_d_include_in_total is not None:
                        earningg_entry["do_not_include_in_total"] = company_d_include_in_total

                    if company_d_full_tax is not None:
                        earningg_entry["deduct_full_tax_on_selected_payroll_date"] = company_d_full_tax
                    
                    if company_ex_from_income_tax is not None:
                        earningg_entry["exempted_from_income_tax"] = company_ex_from_income_tax

                    if company_stastical_component is not None:
                         earningg_entry["statistical_component"] = company_stastical_component
                         

                    # Append the deduction entry to the list
                    self.append("earnings", earningg_entry)

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






########################## Umair's Work ##########################

def set_fix_days(self):
    hr_setting = frappe.db.get_list('Sowaan HR Setting')
    if not hr_setting:
        return
    parent_to_use = get_deduction_parent(self.employee, self.salary_structure)
    if not parent_to_use:
        return

    calculation_criteria = frappe.db.get_value('Sowaan HR Setting', parent_to_use, 'calculation_criteria')
    if calculation_criteria == "Fix Days":
        self.total_working_days = int(frappe.db.get_value('Sowaan HR Setting', parent_to_use, 'days'))
    handle_late_scenario(self, parent_to_use)
        
# Call in salary slip js file
@frappe.whitelist()
def get_deduction_parent(employee, salary_structure):
    if not frappe.db.exists("DocType", "Deduction Employees") or not frappe.db.exists("DocType", "Deduction Salary Structures"):
        return None
    ded_emp_list = frappe.get_all(
        "Deduction Employees",
        filters={"parenttype": "Sowaan HR Setting"},
        fields=["employee", "parent"],
        ignore_permissions=True
    )
    
    ded_ss_list = frappe.get_all(
        "Deduction Salary Structures",
        filters={"parenttype": "Sowaan HR Setting"},
        fields=["salary_structure", "parent"],
        ignore_permissions=True
    )

    
    if not ded_emp_list and not ded_ss_list:
        return None

    emp_dict = {emp["employee"]: emp["parent"] for emp in ded_emp_list if isinstance(emp, dict)}
    ss_dict = {ss["salary_structure"]: ss["parent"] for ss in ded_ss_list if isinstance(ss, dict)}
    if employee not in emp_dict and salary_structure not in ss_dict:
        return None
    
    return emp_dict.get(employee) or ss_dict.get(salary_structure)

        

def handle_late_scenario(self, parent_to_use):
    def update_or_create_deduction(component, amount):
        """Update or create a deduction entry in the deductions list."""
        deductions_dict = {d.salary_component: d for d in self.deductions}

        if component in deductions_dict:
            existing_row = deductions_dict[component]
            existing_row.amount = amount
            if amount == 0:
                self.deductions.remove(existing_row)
        elif amount > 0:
            row = self.append('deductions', {'salary_component': component, 'amount': amount})

    hr_settings = frappe.get_doc('Sowaan HR Setting', parent_to_use)
    if not any([hr_settings.is_late_deduction_applicable,
                hr_settings.is_early_deduction_applicable,
                hr_settings.is_half_day_deduction_applicable]):
        return
    # frappe.throw('hello')
    assign_shift = frappe.db.get_value('Shift Assignment',
        {'employee': self.employee, 'start_date': ['<=', self.start_date]},
        'shift_type', order_by='start_date desc') or frappe.db.get_value('Employee', self.employee, 'default_shift')

    if not assign_shift:
        return

    shift = frappe.db.get_value('Shift Type', assign_shift, ['start_time', 'end_time'], as_dict=True)
    if not shift:
        return

    shift_start_time = shift.start_time
    shift_end_time = shift.end_time
    total_working_days = self.total_working_days

    deduction_base = hr_settings.deduction_based_on.lower() if hr_settings.deduction_based_on else None
    if deduction_base == 'basic':
        ded_salary = next((e.amount for e in self.earnings if e.salary_component.lower() == 'basic'), 0)
    elif deduction_base == 'base':
        salary_structure = frappe.get_all("Salary Structure Assignment",
            filters=[["employee", "=", self.employee], ["from_date", "<=", self.start_date], ["docstatus", "=", 1]],
            fields=['base'], order_by="from_date desc", limit=1)
        ded_salary = salary_structure[0].base if salary_structure else 0
    else:
        return  

    if not ded_salary or ded_salary == 0 or total_working_days == 0:
        return  

    shift_hours = (shift_end_time - shift_start_time).total_seconds() / 3600
    minute_salary = ded_salary / total_working_days / shift_hours / 60
    half_day_salary = ded_salary / total_working_days / 2

    attendance = frappe.db.get_list('Attendance', filters={
        'employee': self.employee,
        'status': ['in', ['Present', 'Half Day']],
        'attendance_date': ['between', [self.start_date, self.end_date]],
        'docstatus': 1
    }, fields=['in_time', 'out_time', 'status', 'late_entry', 'early_exit'], order_by='attendance_date asc')

    if not attendance:
        return

    exemptions = {
        'half_day': hr_settings.get('half_day_exemptions', 0),
        'early_exit': hr_settings.get('early_exit_exemptions', 0),
        'late_entry': hr_settings.get('late_entry_exemptions', 0)
    }

    late_count = early_departure_count = half_day_count = 0
    total_late_minutes = total_early_minutes = deduction_half_day_count = 0
    total_late_count = total_early_departure_count = total_half_day_count = 0

    for a in attendance:
        if not a['in_time'] or not a['out_time']:
            continue

        in_time = timedelta(hours=a['in_time'].hour, minutes=a['in_time'].minute, seconds=a['in_time'].second)
        out_time = timedelta(hours=a['out_time'].hour, minutes=a['out_time'].minute, seconds=a['out_time'].second)

        if hr_settings.is_half_day_deduction_applicable and a['status'] == 'Half Day':
            half_day_count += 1
            if half_day_count > exemptions['half_day']:
                deduction_half_day_count += 1

        if hr_settings.is_early_deduction_applicable and a['status'] == 'Present' and a['early_exit']:
            early_departure_count += 1
            if early_departure_count > exemptions['early_exit']:
                total_early_minutes += (shift_end_time - out_time).seconds // 60
                total_early_departure_count += 1

        if hr_settings.is_late_deduction_applicable and a['status'] == 'Present' and a['late_entry']:
            late_count += 1
            if late_count > exemptions['late_entry']:
                total_late_minutes += (in_time - shift_start_time).seconds // 60
                total_late_count += 1

    self.custom_late_entry_minutes = total_late_minutes
    self.custom_early_exit_minutes = total_early_minutes
    self.custom_total_half_days = half_day_count

    if hr_settings.calculation_method == 'Minutes':
        update_or_create_deduction(hr_settings.late_salary_component, total_late_minutes * minute_salary)
        update_or_create_deduction(hr_settings.early_salary_component, total_early_minutes * minute_salary)
        update_or_create_deduction(hr_settings.half_day_salary_component, deduction_half_day_count * half_day_salary)
    elif hr_settings.calculation_method == 'Counts':
        if hr_settings.late_deduction_factor and hr_settings.late_deduction_factor != 0:
            update_or_create_deduction(hr_settings.late_salary_component, total_late_count * hr_settings.late_deduction_factor * (ded_salary / total_working_days))
        else:
            update_or_create_deduction(hr_settings.late_salary_component, total_late_count * minute_salary)

        if hr_settings.early_deduction_factor and hr_settings.early_deduction_factor != 0:
            update_or_create_deduction(hr_settings.early_salary_component, total_early_departure_count * hr_settings.early_deduction_factor * (ded_salary / total_working_days))
        else:
            update_or_create_deduction(hr_settings.early_salary_component, total_early_departure_count * minute_salary)

        if hr_settings.half_day_deduction_factor and hr_settings.half_day_deduction_factor != 0:
            update_or_create_deduction(hr_settings.half_day_salary_component, total_half_day_count * hr_settings.half_day_deduction_factor * (ded_salary / total_working_days))
        else:
            update_or_create_deduction(hr_settings.half_day_salary_component, total_half_day_count * half_day_salary)

    self.calculate_net_pay()
    self.compute_year_to_date()
    self.compute_month_to_date()
    self.compute_component_wise_year_to_date()








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
        

def before_save_salaryslip(doc,method):

    if frappe.db.get_value('Employee', doc.employee, 'custom_allow_overtime'): 
        recalculate = True
        ot_hours_list = frappe.get_all("Employee Overtime",filters={
                        "employee": ["=", doc.employee],
                        "overtime_date": ["Between", [doc.start_date,doc.end_date]],
                        "docstatus": ["=", 1]
                        },fields=['approved_overtime_hours'])
                        
        ot_sum = 0
        if len(ot_hours_list) > 0 : 
            for item in ot_hours_list:        
                ot_sum = item.approved_overtime_hours + ot_sum
            doc.custom_ot_hours = ot_sum
            


