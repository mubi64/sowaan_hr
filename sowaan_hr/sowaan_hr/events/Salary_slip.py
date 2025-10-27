import frappe
from hrms.payroll.doctype.salary_slip.salary_slip import (SalarySlip, calculate_tax_by_tax_slab)
from sowaan_hr.sowaan_hr.api.api import create_salary_adjustment_for_negative_salary
from datetime import datetime, timedelta
from frappe.utils import cint, flt
from frappe.query_builder import DocType
from frappe import (_,utils)
from frappe.utils import today
from frappe.utils import nowdate
from hrms.hr.doctype.leave_application.leave_application import get_leave_details
#from erpnext.hr.doctype.leave_ledger_entry.leave_ledger_entry import create_leave_ledger_entry
#from erpnext.hr.doctype.leave_application.leave_application import get_leave_details

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

        fc_start_date = contribution_doc.start_date
        fc_start_date = frappe.utils.getdate(fc_start_date)
        
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
                    if row.contribution_type == "Own" and row.document_name == self.name:
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
                    if row.contribution_type == "Company" and row.document_name == self.name:
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
                        if row.contribution_type == "Own" and row.document_name == self.name:
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
                        if row.contribution_type == "Company" and row.document_name == self.name:
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
                    if row.contribution_type == "Own" and row.document_name == self.name:
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
                        if row.contribution_type == "Company" and row.document_name == self.name:
                            frappe.db.set_value("Fund Contribution Entry", row.name, "amount", total_fund_amount2)
                            break

   
 

    set_fix_days(self)
    before_save_salaryslip(self)

    self.custom_check_adjustment = 0
    self.calculate_net_pay()
    self.compute_year_to_date()
    self.compute_month_to_date()
    self.compute_component_wise_year_to_date()




def salary_slip_after_submit(self,method):
    fund_contribution = frappe.get_list(
            "Fund Contribution",
            filters={
                "employee": self.employee,
                "docstatus": 1
            },
            fields=["name", "fund_setting"]
        )
    if fund_contribution:
        own_fund_value = 0
        company_fund_value = 0

        contribution_doc = frappe.get_doc("Fund Contribution", fund_contribution[0].get("name"))
        fund_setting_name = fund_contribution[0].get("fund_setting")

        if not fund_setting_name:
            return
        
        fund_setting = frappe.get_doc("Fund Setting", fund_setting_name)
        own_component_name = fund_setting.fund_component or ""
        company_component_name = fund_setting.company_fund_component or ""

        for row in self.get("deductions", []):
            if row.salary_component == own_component_name:
                own_fund_value = row.amount or 0
                break
        for row in self.get("earnings", []):
            if row.salary_component == company_component_name:
                company_fund_value = row.amount or 0
                break

        found_own_entry = False

        for row in contribution_doc.get("fund_contribution_entry", []):
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
        for row in contribution_doc.get("fund_contribution_entry", []):
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

    # after submit netpay update on payroll entry if payroll entry exist
    if self.payroll_entry:
        frappe.db.sql(
            """
            UPDATE `tabPayroll Employee Detail`
            SET custom_payable = %s
            WHERE parent = %s and employee = %s
            """,
            (self.net_pay or 0, self.payroll_entry, self.employee),
        )

def on_cancel(self, method):
    if self.payroll_entry:
        frappe.db.sql(
            """
            UPDATE `tabPayroll Employee Detail`
            SET custom_payable = %s
            WHERE parent = %s and employee = %s
            """,
            (0, self.payroll_entry, self.employee),
        )

########################## Umair's Work ##########################

def set_fix_days(self):
    
    hr_setting = frappe.db.get_list('Sowaan HR Setting')
    if not hr_setting:
        return
    parent_to_use = get_deduction_parent(self.employee, self.salary_structure)
    #frappe.msgprint(f"parent_to_use {parent_to_use}")
    
    if not parent_to_use:
        return

    # frappe.msgprint(f"Start Date {self.start_date} End Date {self.end_date}")
    # return
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
    #frappe.msgprint(f"Deduction Employees {ded_emp_list}")

    ded_ss_list = frappe.get_all(
        "Deduction Salary Structures",
        filters={"parenttype": "Sowaan HR Setting"},
        fields=["salary_structure", "parent"],
        ignore_permissions=True
    )

    #frappe.msgprint(f"Deduction Salary Structure {ded_ss_list}")
    

    if not ded_emp_list and not ded_ss_list:
        return None

    emp_dict = {emp["employee"]: emp["parent"] for emp in ded_emp_list if isinstance(emp, dict)}
    ss_dict = {ss["salary_structure"]: ss["parent"] for ss in ded_ss_list if isinstance(ss, dict)}

    if employee not in emp_dict and salary_structure not in ss_dict:
        return None
    
    return emp_dict.get(employee) or ss_dict.get(salary_structure)

        

def handle_late_scenario(self, parent_to_use):
    def create_additional_salary(component_name, amount):
        """Fetch component, ensure company is in accounts, then create Additional Salary."""
        if amount == 0:
            return
        
        #frappe.msgprint(f"Amount {amount} Component_name {component_name}......")
        existing = frappe.db.exists(
            "Additional Salary",
            {
                "employee": self.employee,
                "salary_component": component_name,
                "from_date": self.start_date,
                "to_date": self.end_date,
                "company": self.company,
                "docstatus": 1  
            }
        )
        
        if existing:
            existing_amount = frappe.db.get_value(
                "Additional Salary",
                existing,
                "amount"
            )
            # if flt(existing_amount) == flt(amount):
            #     return

            as_doc = frappe.get_doc("Additional Salary", existing)
            as_doc.ignore_permissions = True
            as_doc.cancel()
            existing_row = next((d for d in self.deductions if d.salary_component == component_name), None)
            if existing_row:
                self.deductions.remove(existing_row)


        # check_attendance = frappe.db.get_list('Attendance', filters={
        # 'employee': self.employee,
        # 'status': ['in', ['Present', 'Half Day']],
        # 'attendance_date': ['between', [self.start_date, self.end_date]],
        # 'docstatus': 1
        # }, fields=['in_time', 'out_time', 'status', 'late_entry', 'early_exit', 'attendance_date'], order_by='attendance_date asc')

      
        # if check_attendance:
        #    for x in attendance:
        #         if check_late_approval(self.employee, x['attendance_date']):
        #             #frappe.msgprint(f"Late is approved in attendance for {self.employee}")
        #             continue  # skip this record and move to next     
    
        component = frappe.get_doc("Salary Component", component_name)
        if not any(acc.company == self.company for acc in component.accounts):
            default_account = frappe.get_cached_value(
                "Company",
                self.company,
                "default_payroll_payable_account"
            )
            component.append("accounts", {
                "company": self.company,
                "account": default_account
            })
            component.save()

        

        additional_salary = frappe.get_doc({
            "doctype": "Additional Salary",
            "employee": self.employee,
            "salary_component": component.name,
            "is_recurring": 1,
            "from_date": self.start_date,
            "to_date": self.end_date,
            "currency": self.currency,
            "amount": amount,
            "company": self.company,
            "overwrite_salary_structure_amount": 1
        })
        additional_salary.insert(ignore_permissions=True)
        additional_salary.submit()
        #frappe.msgprint(f"submitting.... {amount} Component_name {component_name}......")
            
        # deductions_dict = {d.salary_component: d for d in self.deductions}
        # # frappe.msgprint(str(deductions_dict))

        # if component in deductions_dict:
        #     existing_row = deductions_dict[component]
        #     existing_row.amount = amount
        #     if amount == 0:
        #         self.deductions.remove(existing_row)
        # elif amount > 0:
        #     # frappe.msgprint(str(component))
        #     # frappe.msgprint(str(amount))
        #     self.append('deductions', {'salary_component': component, 'amount': amount})
        # frappe.msgprint(str({d.salary_component: d for d in self.deductions}))

    

    hr_settings = frappe.get_doc('Sowaan HR Setting', parent_to_use)
    if not any([hr_settings.is_late_deduction_applicable,
                hr_settings.is_early_deduction_applicable,
                hr_settings.is_half_day_deduction_applicable]):
        return
    # frappe.throw('funchello')
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
        ded_salary = next((e.amount for e in self.earnings if 'basic' in e.salary_component.lower()), 0)
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
    }, fields=['in_time', 'out_time', 'status', 'late_entry', 'early_exit', 'attendance_date'], order_by='attendance_date asc')

      
    if not attendance:
        return


    late_flag_count = cint(hr_settings.get('late_flag_count', 0))
    early_flag_count = cint(hr_settings.get('early_flag_count', 0))
    half_day_flag_count = cint(hr_settings.get('half_day_flag_count', 0))



    exemptions = {
        'half_day': cint(hr_settings.get('half_day_exemptions', 0)),
        'early_exit': cint(hr_settings.get('early_exit_exemptions', 0)),
        'late_entry': cint(hr_settings.get('late_entry_exemptions', 0))
    }


    late_count = early_departure_count = half_day_count = 0
    total_late_minutes = total_early_minutes = 0
    total_late_count = total_early_departure_count = deduction_half_day_count = 0
    
    half_day_violations = []
    early_departure_violations = []
    late_arrival_violations = []   
    

    for a in attendance:
        # frappe.msgprint(f"in_time{a['in_time'] } out_time {a['out_time']}")
    
        # frappe.msgprint(f"Attendance {attendance}")
        if not a['in_time'] or not a['out_time']:
            #frappe.msgprint(f"In Tme....{a['in_time']} ...Out time {a['out_time']} ... Status {a['status']}")
            continue

        in_time = timedelta(hours=a['in_time'].hour, minutes=a['in_time'].minute, seconds=a['in_time'].second)
        out_time = timedelta(hours=a['out_time'].hour, minutes=a['out_time'].minute, seconds=a['out_time'].second)     
       
        
        
        ## Half Day Work ##
        #frappe.msgprint(f"Status....{a['status']}")
        if hr_settings.is_half_day_deduction_applicable and a['status'] == 'Half Day':
            #frappe.msgprint(f"Status....{a['status']}")
            half_day_count += 1

            if half_day_count < half_day_flag_count + exemptions["half_day"]:
                pass
            else:
                excess_half_days = flt(half_day_count) - flt(half_day_flag_count)
                if half_day_flag_count == 0:
                    deduction_half_day_count += 1
                    half_day_violations.append({
                        "date": a['attendance_date'],
                        "half_day": 1                        
                    })
                elif excess_half_days % half_day_flag_count == 0:
                    deduction_half_day_count += 1
                    half_day_violations.append({
                        "date": a['attendance_date'],
                        "half_day": 1                        
                    })
        ## Early Work ##
        if hr_settings.is_early_deduction_applicable and a['status'] == 'Present' and a['early_exit']:
            early_departure_count += 1
            if early_departure_count < early_flag_count + exemptions["early_exit"]: 
                pass
            else:
                excess_early_days = early_departure_count - early_flag_count
                if early_flag_count == 0:
                    total_early_minutes += (shift_end_time - out_time).seconds // 60
                    total_early_departure_count += 1
                    early_departure_violations.append({
                        "date": a['attendance_date'],
                        "early_departure": 1                        
                    })
                elif excess_early_days % early_flag_count == 0:
                    total_early_minutes += (shift_end_time - out_time).seconds // 60
                    total_early_departure_count += 1
                    early_departure_violations.append({
                        "date": a['attendance_date'],
                        "early_departure": 1                        
                    })
                    
        ## Late Work ##
        if hr_settings.is_late_deduction_applicable and a['status'] == 'Present' and a['late_entry']:         
                
                if check_late_approval(self.employee, a['attendance_date']):
                    #frappe.msgprint(f"Late is approved in attendance for {self.employee}")
                    continue  # skip this record and move to next                

                late_count += 1

                if late_count < late_flag_count + exemptions["late_entry"]:
                    pass
                else:
                    excess_late_days = late_count - late_flag_count
                    ## if condition neccessary (flag_count == 0) ##
                    if late_flag_count == 0:
                        total_late_minutes += (in_time - shift_start_time).seconds // 60
                        total_late_count += 1 
                        #frappe.msgprint(f"Late is approved in attendance for {a['attendance_date']}")
                        late_arrival_violations.append({
                            "date": a['attendance_date'],
                            "late_arrival": 1                        
                        })
                    elif excess_late_days % late_flag_count == 0:
                        total_late_minutes += (in_time - shift_start_time).seconds // 60
                        total_late_count += 1
                        #frappe.msgprint(f"Late is approved in attendance for {a['attendance_date']}")
                        late_arrival_violations.append({
                            "date": a['attendance_date'],
                            "late_arrival": 1                        
                        })





        # if hr_settings.is_late_deduction_applicable and a['status'] == 'Present' and a['late_entry']:
        #     late_count += 1
        #     if late_count < late_flag_count:
        #         pass
        #     elif late_count < late_flag_count + exemptions["late_entry"]:
        #         pass
        #     else:
        #         excess_late_days = late_count - (late_flag_count + exemptions["late_entry"])
        #         if late_flag_count == 0:
        #             total_late_minutes += (in_time - shift_start_time).seconds // 60
        #             total_late_count += 1
        #         elif excess_late_days > 0 and excess_late_days % late_flag_count == 0:
        #             total_late_minutes += (in_time - shift_start_time).seconds // 60
        #             total_late_count += 1




        


    # frappe.throw(str(total_late_count))
    # frappe.throw(str(late_count))
    self.custom_late_entry_counts = late_count
    self.custom_early_exit_counts = early_departure_count
    self.custom_deductible_late_entry_counts = total_late_count
    self.custom_deductible_early_exit_counts = total_early_departure_count
    self.custom_deductible_half_days = deduction_half_day_count
    self.custom_late_entry_minutes = total_late_minutes
    self.custom_early_exit_minutes = total_early_minutes
    self.custom_total_half_days = half_day_count

    if hr_settings.calculation_method == 'Minutes':
        if hr_settings.is_late_deduction_applicable:
            create_additional_salary(hr_settings.late_salary_component, total_late_minutes * minute_salary)
        if hr_settings.is_early_deduction_applicable:
            create_additional_salary(hr_settings.early_salary_component, total_early_minutes * minute_salary)
        if hr_settings.is_half_day_deduction_applicable:
            create_additional_salary(hr_settings.half_day_salary_component, deduction_half_day_count * half_day_salary)
    elif hr_settings.calculation_method == 'Counts':
        
        #if late deduction is applicable
        if hr_settings.is_late_deduction_applicable and hr_settings.deduct_from_leaves and late_arrival_violations:
            
            #frappe.msgprint(f"Total Late Count In Late{total_late_count}") 
            #add new condition here.... if duduct from leaves is selected then adjust late in leaves
              
            #if deduct from leaves late deduction factor are selected and late deduction factor is not 0
            if  hr_settings.late_deduction_factor and hr_settings.late_deduction_factor != 0:               
               remaining_deduction = check_late_application(self.employee, late_arrival_violations, hr_settings.late_deduction_factor)

            #    frappe.msgprint(f"Remaining Reduction {remaining_deduction}") 
            #    return
               if remaining_deduction and remaining_deduction > 0:  
                    #if not sufficient leaves are left for adjustment then adjust in salary                  
                    if hr_settings.late_deduction_factor and hr_settings.late_deduction_factor != 0:
                        create_additional_salary(hr_settings.late_salary_component, remaining_deduction * (ded_salary / total_working_days))
                    else:                        
                        create_additional_salary(hr_settings.late_salary_component, remaining_deduction * minute_salary)
               else: 
                    frappe.msgprint("✅ All late deductions adjusted in leaves. No salary deduction required.")  
            else:
                if hr_settings.late_deduction_factor and hr_settings.late_deduction_factor != 0:                    
                    create_additional_salary(hr_settings.late_salary_component, total_late_count * hr_settings.late_deduction_factor * (ded_salary / total_working_days))
                else:                   
                    create_additional_salary(hr_settings.late_salary_component, total_late_count * minute_salary)
        else:
                if hr_settings.late_deduction_factor and hr_settings.late_deduction_factor != 0:                   
                    create_additional_salary(hr_settings.late_salary_component, total_late_count * hr_settings.late_deduction_factor * (ded_salary / total_working_days))
                else:                    
                    create_additional_salary(hr_settings.late_salary_component, total_late_count * minute_salary)
        #end of late deduction case

        #if early deduction is applicable            
        if hr_settings.is_early_deduction_applicable and hr_settings.custom_early_deduct_from_leaves and early_departure_violations:

            #add new condition here.... if duduct from leaves is selected then adjust early in leaves

            #if deduct from leaves early deduction factor are selected and early deduction factor is not 0
            if hr_settings.custom_early_deduct_from_leaves and hr_settings.early_deduction_factor and hr_settings.early_deduction_factor != 0:               
               #adjust in leaves
               remaining_deduction = check_early_application(self.employee, early_departure_violations, hr_settings.early_deduction_factor)
            #    frappe.msgprint(f"Remaining Reduction {remaining_deduction}")             
            #    return
               if remaining_deduction and remaining_deduction > 0:  
                    #if not sufficient leaves are left for adjustment then adjust in salary                  
                    if hr_settings.early_deduction_factor and hr_settings.early_deduction_factor != 0:
                        create_additional_salary(hr_settings.early_salary_component, remaining_deduction * (ded_salary / total_working_days))
                    else:
                        create_additional_salary(hr_settings.early_salary_component, remaining_deduction * minute_salary)
            else:
                if hr_settings.early_deduction_factor and hr_settings.early_deduction_factor != 0:
                    create_additional_salary(hr_settings.early_salary_component, total_early_departure_count * hr_settings.early_deduction_factor * (ded_salary / total_working_days))
                else:
                    create_additional_salary(hr_settings.early_salary_component, total_early_departure_count * minute_salary)
        else:
            if hr_settings.early_deduction_factor and hr_settings.early_deduction_factor != 0:
                create_additional_salary(hr_settings.early_salary_component, total_early_departure_count * hr_settings.early_deduction_factor * (ded_salary / total_working_days))
            else:
                create_additional_salary(hr_settings.early_salary_component, total_early_departure_count * minute_salary)
        #end early arrival deduction case

        #if half day deduction is applicable      
        # frappe.msgprint(f"halfday_deduction_factor {half_day_violations}")    
        # frappe.msgprint(f"is_half_day_deduction_applicable {hr_settings.is_half_day_deduction_applicable}") 
        # frappe.msgprint(f"hr_settings.custom_half_day_deduct_from_leaves {hr_settings.custom_half_day_deduct_from_leaves}") 

        if hr_settings.is_half_day_deduction_applicable and hr_settings.custom_half_day_deduct_from_leaves and half_day_violations:
            #frappe.msgprint(f"In Half Day deduction")     
            #add new condition here.... if duduct from leaves is selected then adjust half day in leaves

            #if deduct from leaves half day deduction factor are selected and half day deduction factor is not 0
            if hr_settings.custom_half_day_deduct_from_leaves and hr_settings.half_day_deduction_factor and hr_settings.half_day_deduction_factor != 0:               
               #adjust in leaves
               remaining_deduction = check_halfday_application(self.employee, half_day_violations, hr_settings.half_day_deduction_factor)
               #frappe.msgprint(f"Remaining Reduction {remaining_deduction}")             
            #    return 
               if remaining_deduction and remaining_deduction > 0:  
                    #if not sufficient leaves are left for adjustment then adjust in salary                  
                    if hr_settings.half_day_deduction_factor and hr_settings.half_day_deduction_factor != 0:
                        create_additional_salary(hr_settings.half_day_salary_component, remaining_deduction * (ded_salary / total_working_days))
                    else:
                        create_additional_salary(hr_settings.half_day_salary_component, remaining_deduction * minute_salary)
            else:
                if hr_settings.half_day_deduction_factor and hr_settings.half_day_deduction_factor != 0:
                    create_additional_salary(hr_settings.half_day_salary_component, deduction_half_day_count * hr_settings.half_day_deduction_factor * (ded_salary / total_working_days))
                else:
                    create_additional_salary(hr_settings.half_day_salary_component, deduction_half_day_count * minute_salary)
        #end of half day deduction case
        else:
            if hr_settings.is_half_day_deduction_applicable:
                if hr_settings.half_day_deduction_factor and hr_settings.half_day_deduction_factor != 0:
                    create_additional_salary(hr_settings.half_day_salary_component, deduction_half_day_count * hr_settings.half_day_deduction_factor * (ded_salary / total_working_days))
                else:
                    create_additional_salary(hr_settings.half_day_salary_component, deduction_half_day_count * minute_salary)
                    
    self.calculate_net_pay()
    self.compute_year_to_date()
    self.compute_month_to_date()
    self.compute_component_wise_year_to_date()


@frappe.whitelist()

#check if leave application already exist
def check_late_application(employee, violations, late_deduction_factor):
    
    try:
        attendance_date = today()        

        #frappe.msgprint(f"late_arrival_violations {violations}") 

        if not violations:
            frappe.msgprint("No violations found — no leave adjustments needed.")
            return
    
        for v in violations:
            attendance_date = v["date"]
            deduction = v["late_arrival"]

            #frappe.msgprint(f"Attendance Date: {attendance_date}")

            #total_late_days = deduction * late_deduction_factor
            total_late_days = round(deduction * late_deduction_factor, 2)
            #frappe.msgprint(f"Total Late Days: {total_late_days}")

            if not employee or not total_late_days:
                frappe.throw("Employee and total late days are required")  

            frappe.msgprint(f"Late deduction process started for Employee: {employee}")

            frappe.msgprint(f"Late Days {total_late_days}")

            remaining_deduction = total_late_days            
            
            if remaining_deduction <= 0:
                frappe.throw("Deduction days must be greater than zero.")

            #for lt in leave_types:
            if remaining_deduction <= 0:
                break

            # Check if leave already exists for this employee and date
            existing_leave = frappe.db.exists(
            "Leave Application",
            {
                "employee": employee,
                "from_date": attendance_date,
                "to_date": attendance_date,
                "docstatus": 1  # only submitted leaves
            }
    )
            if existing_leave:
               remaining_deduction -= deduction 

            elif not existing_leave:
                frappe.msgprint(
                f"⚠️ No Leave Application found for {attendance_date}. Remaining deduction: {remaining_deduction}"                
            )
                frappe.msgprint(f"remaining balance ⚠️ {remaining_deduction} day(s).")    
                return remaining_deduction  # stop and send remaining deduction
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error: {error_msg}")
        frappe.log_error("Error in late adjustment in leaves", str(e))

#check if leave application already exist
def check_early_application(employee, violations, early_deduction_factor):
   
    try:
        attendance_date = today()        

        #frappe.msgprint(f"late_arrival_violations {violations}") 

        if not violations:
            frappe.msgprint("No violations found — no leave adjustments needed.")
            return
    
        for v in violations:
            attendance_date = v["date"]
            deduction = v["early_departure"]

            #frappe.msgprint(f"Attendance Date: {attendance_date}")

            #total_early_days = deduction * late_deduction_factor
            total_early_days = round(deduction * early_deduction_factor, 2)
            #frappe.msgprint(f"Total Late Days: {total_late_days}")

            if not employee or not total_early_days:
                frappe.throw("Employee and total early days are required")  

            frappe.msgprint(f"Early leave check process started for Employee: {employee}")

            #frappe.msgprint(f"Early Days {total_early_days}")

            remaining_deduction = total_early_days            
            
            if remaining_deduction <= 0:
                frappe.throw("Deduction days must be greater than zero.")

            #for lt in leave_types:
            if remaining_deduction <= 0:
                break

            # Check if leave already exists for this employee and date
            existing_leave = frappe.db.exists(
            "Leave Application",
            {
                "employee": employee,
                "from_date": attendance_date,
                "to_date": attendance_date,
                "docstatus": 1  # only submitted leaves
            }
    )
            if existing_leave:
               remaining_deduction -= deduction 

            elif not existing_leave:
                frappe.msgprint(
                f"⚠️ No Leave Application found for {attendance_date}. Remaining deduction: {remaining_deduction}"                
            )
                frappe.msgprint(f"remaining balance ⚠️ {remaining_deduction} day(s).")    
                return remaining_deduction  # stop and send remaining deduction
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error: {error_msg}")
        frappe.log_error("Error in early adjustment in leaves", str(e))

#check if leave application already exist
def check_halfday_application(employee, violations, halfday_deduction_factor):
   
    try:
        attendance_date = today()        

        #frappe.msgprint(f"halfday_deduction_factor {violations}") 

        if not violations:
            frappe.msgprint("No violations found — no leave adjustments needed.")
            return
    
        for v in violations:
            attendance_date = v["date"]
            deduction = v["half_day"]

            #frappe.msgprint(f"Attendance Date: {attendance_date}")

            #total_half_days = deduction * late_deduction_factor
            total_half_days = round(deduction * halfday_deduction_factor, 2)

            #frappe.msgprint(f"Total Half Days: {total_half_days}")

            if not employee or not total_half_days:
                frappe.throw("Employee and total half days are required")  

            frappe.msgprint(f"Half leave check process started for Employee: {employee}")

            #frappe.msgprint(f"Half Days {total_half_days}")

            remaining_deduction = total_half_days            
            
            if remaining_deduction <= 0:
                frappe.throw("Deduction days must be greater than zero.")

            #for lt in leave_types:
            if remaining_deduction <= 0:
                break

            # Check if leave already exists for this employee and date
            existing_leave = frappe.db.exists(
            "Leave Application",
            {
                "employee": employee,
                "from_date": attendance_date,
                "to_date": attendance_date,
                "docstatus": 1  # only submitted leaves
            }
    )
            if existing_leave:
               remaining_deduction -= deduction 

            elif not existing_leave:
                frappe.msgprint(
                f"⚠️ No Leave Application found for {attendance_date}. Remaining deduction: {remaining_deduction}"                
            )
                frappe.msgprint(f"remaining balance ⚠️ {remaining_deduction} day(s).")    
                return remaining_deduction  # stop and send remaining deduction
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error: {error_msg}")
        frappe.log_error("Error in half days leaves", str(e))

def check_late_approval(employee, late_date):    

    
    """Check if attendance exists and late is approved"""
    att = frappe.db.get_value(
        "Attendance",
        {"employee": employee, "attendance_date": late_date},
        ["late_entry", "late_approved"],
        as_dict=True,
    )        

    #frappe.msgprint(f"Attendance {att}")

    if not att:
        return False  # no attendance found

    if att.late_entry and att.late_approved:
        frappe.msgprint(f"Late is approved in attendance for {employee} on {late_date}")

        frappe.logger().info(f"Late is approved in attendance for {employee} on {late_date}")
        return True

    

def before_delete(self):
    
    # Find all leave applications linked to this Salary Slip
    linked_leaves = frappe.get_all(
        "Leave Application",
        filters={"custom_salary_slip_reference": self.name},
        fields=["name", "docstatus"]
    )

    for leave in linked_leaves:
        leave_doc = frappe.get_doc("Leave Application", leave.name)
        
        # Cancel if submitted
        if leave_doc.docstatus == 1:
            leave_doc.cancel()
        
        # Delete leave (or unlink if you prefer to keep record)
        frappe.delete_doc("Leave Application", leave_doc.name, force=1)
        
        # Also unlink attendance records
        attendance_list = frappe.get_all(
            "Attendance",
            filters={"leave_application": leave_doc.name},
            pluck="name"
        )
    for att_name in attendance_list:
        try:
            att_doc = frappe.get_doc("Attendance", att_name)
            # Cancel attendance if submitted
            if att_doc.docstatus == 1:
                att_doc.cancel()
                # If not submitted, delete it
            elif att_doc.docstatus == 0:
                    frappe.delete_doc("Attendance", att_name, force=1)    
        except Exception as e:
                    frappe.log_error(f"Error canceling/deleting attendance {att_name}: {e}")


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
        

def before_save_salaryslip(doc):
    if frappe.db.get_value('Employee', doc.employee, 'custom_allow_overtime'): 
        recalculate = True
        EmployeeOvertime = DocType("Employee Overtime")
        ot_hours_list = (
            frappe.qb.from_(EmployeeOvertime)
            .select(EmployeeOvertime.approved_overtime_hours)
            .where(
                (EmployeeOvertime.employee == doc.employee)
                & (EmployeeOvertime.overtime_date.between(doc.start_date, doc.end_date))
                & (EmployeeOvertime.docstatus == 1)
            )
        ).run(as_dict=True)                       

        ot_sum = 0
        if len(ot_hours_list) > 0 : 
            for item in ot_hours_list:        
                ot_sum = flt(item.approved_overtime_hours) + flt(ot_sum)
            doc.custom_ot_hours = ot_sum

        shift_req_hrs = 0
        shift_name = None
        holiday_list_name = None
        holiday_dates = []
        holiday_overtime_hrs = 0
        shift_ass_list = frappe.db.get_list('Shift Assignment' , 
                            filters={
                                'employee' : doc.employee ,
                                'status' : 'Active' ,
                                'start_date' : ['<' , doc.end_date] ,
                            },
                            fields = ['name','shift_type'] ,
                            order_by = 'start_date desc'
                          )
        if shift_ass_list :
            shift_name = shift_ass_list[0].shift_type
            shift_req_hrs = frappe.db.get_value('Shift Type', shift_name, 'required_hours')
            holiday_list_name = frappe.db.get_value('Shift Type', shift_name, 'holiday_list')
        
        else :
            shift_name = frappe.db.get_value('Employee' , doc.employee , 'default_shift')
            if shift_name :
                shift_req_hrs = frappe.db.get_value('Shift Type', shift_name, 'required_hours')
                holiday_list_name = frappe.db.get_value('Shift Type', shift_name, 'holiday_list')


        if holiday_list_name :
            holiday_list_doc = frappe.get_doc('Holiday List', holiday_list_name)
            holiday_dates = [holiday.holiday_date for holiday in holiday_list_doc.holidays]

        else :
            holiday_list_name = frappe.db.get_value('Employee' , doc.employee , 'holiday_list')
            holiday_list_doc = frappe.get_doc('Holiday List', holiday_list_name)
            holiday_dates = [holiday.holiday_date for holiday in holiday_list_doc.holidays]


        emp_ovrtime_list = (
                        frappe.qb.from_(EmployeeOvertime)
                        .select(EmployeeOvertime.approved_overtime_hours)
                        .where(
                            (EmployeeOvertime.employee == doc.employee)
                            & (EmployeeOvertime.overtime_date.between(doc.start_date, doc.end_date))
                            & (EmployeeOvertime.overtime_date.isin(holiday_dates))
                            & (EmployeeOvertime.docstatus == 1)
                        )
                    ).run(as_dict=True)

        if emp_ovrtime_list :
            for row in emp_ovrtime_list :
                holiday_overtime_hrs = flt(holiday_overtime_hrs) + flt(row.approved_overtime_hours)


        doc.custom_overtime_hours_on_working_day = flt(doc.custom_ot_hours) - flt(holiday_overtime_hrs)
        doc.custom_overtime_hours_on_holiday = holiday_overtime_hrs


        base = frappe.get_list('Salary Structure Assignment',
                filters = {
                    'employee' : doc.employee ,
                    'salary_structure' : doc.salary_structure ,
                    'from_date' : ['<' , doc.end_date]  ,
                    'docstatus' : 1 ,
                },
                fields=['base'],
                order_by='from_date desc',
            )
       
        if base :
            one_zero = 1
            if shift_req_hrs == 0 :
                shift_req_hrs = 1
                one_zero = 0

            working_days_for_overtime = 30

            overtime_based_on = frappe.db.get_single_value('SowaanHR Payroll Settings','overtime_based_on')
            if overtime_based_on == 'Working Days' :
                working_days_for_overtime = doc.total_working_days

            else :
                working_days_for_overtime = frappe.db.get_single_value('SowaanHR Payroll Settings','fixed_days')

            overtime_rate_on_working_days = frappe.db.get_single_value('SowaanHR Payroll Settings','overtime_hours_rate_on_working_day')
            overtime_rate_on_holidays = frappe.db.get_single_value('SowaanHR Payroll Settings','overtime_hours_rate_on_holiday')

            if working_days_for_overtime and shift_req_hrs:
                base_amount = ((flt(base[0].base) / flt(working_days_for_overtime)) / flt(shift_req_hrs)) * flt(one_zero)
            else:
                base_amount = 0

            doc.custom_overtime_per_hour_rate_for_working_day = (flt(base_amount) * flt(overtime_rate_on_working_days)) * flt(doc.custom_overtime_hours_on_working_day)
            doc.custom_overtime_per_hour_rate_for_holiday = (flt(base_amount) * flt(overtime_rate_on_holidays)) * flt(doc.custom_overtime_hours_on_holiday)
    

def own_fund_tax(self,method):
    doc = self
    fund_contribution = frappe.get_list(
            "Fund Contribution",
            filters={
                "employee": self.employee,
                "docstatus": 1
            },
            fields=["*"],

        )

    if fund_contribution:
        tax_component = None
        contribution_doc = frappe.get_doc("Fund Contribution", fund_contribution[0])
        fund_setting_name = contribution_doc.fund_setting
        fund_setting = frappe.get_doc("Fund Setting", fund_setting_name)
        if fund_setting.is_taxable == 1:
            tax_component = fund_setting.tax_component
            Contribution = None  # Using None to indicate if no match is found
            total = None
            for component in doc.deductions:
                
                if component.salary_component == tax_component:
                
                    Contribution = component.amount
                    Contribution = Contribution * 12
                    total = Contribution
                    if total > 150000:
                        Contribution = Contribution - 150000
                        break  

                
            if Contribution is not None and total > 150000:
                Contribution = Contribution / 12
                earning_entry = {
                    "salary_component": tax_component,
                    "amount": Contribution,
                    "year_to_date": Contribution
                }
            self.append("earnings", earning_entry)

            doc.calculate_net_pay()
            doc.compute_year_to_date()
            doc.compute_month_to_date()
            doc.compute_component_wise_year_to_date()