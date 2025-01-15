import frappe
from hrms.payroll.doctype.salary_slip.salary_slip import (SalarySlip, calculate_tax_by_tax_slab)
from sowaan_hr.sowaan_hr.api.api import create_salary_adjustment_for_negative_salary
from frappe.utils import flt

class EmployeeSalarySlip(SalarySlip):
    def update_payment_status_for_gratuity(self):
        additional_salary = frappe.db.get_all(
            "Additional Salary",
            filters={
                "payroll_date": ("between", [self.start_date, self.end_date]),
                "employee": self.employee,
                "ref_doctype": "KSA Gratuity",
                "docstatus": 1,
            },
            fields=["ref_docname", "name"],
            limit=1,
        )

        if additional_salary:
            status = "Paid" if self.docstatus == 1 else "Unpaid"
            if additional_salary[0].name in [entry.additional_salary for entry in self.earnings]:
                frappe.db.set_value("KSA Gratuity", additional_salary[0].ref_docname, "status", status)

    def get_tax_paid_in_period(self, start_date, end_date, tax_component):
		# find total_tax_paid, tax paid for benefit, additional_salary
        total_tax_paid = self.get_salary_slip_details(
            start_date,
            end_date,
            parentfield="deductions",
            salary_component=tax_component,
            variable_based_on_taxable_salary=1,
        )

        tax_deducted_till_date = self.get_opening_for("tax_deducted_till_date", start_date, end_date)

        # Minus the amount from annual tax that is already paid to tax authorities
        total_extra_tax = 0
        if frappe.db.exists("DocType", "Paid Income Tax"):
            total_extra_tax = flt(frappe.db.sql("""
                select 
                    sum(pit.amount) 
                from 
                    `tabPaid Income Tax` pit
                where
                    pit.docstatus=1
                    and %(from_date)s>=pit.period_from
                    and  %(to_date)s<=pit.period_to
                    and pit.employee=%(employee)s
            """,{
                "employee": self.employee,
                "from_date": start_date,
                "to_date": end_date
            })[0][0])

        # Minus the previous additional monthly tax
        extra_current_tax_amount = 0
        if frappe.db.exists("DocType", "Paid Income Tax Monthly"):
            extra_current_tax_amount = flt(frappe.db.sql("""
                select 
                    sum(pitm.amount) 
                from 
                    `tabPaid Income Tax Monthly` pitm
                where
                    pitm.docstatus=1
                    and %(from_date)s>=pitm.period_from
                    and  %(to_date)s<=pitm.period_to
                    and pitm.payroll_date < %(from_date)s
                    and pitm.payroll_date < %(to_date)s
                    and pitm.employee=%(employee)s
            """,{
                "employee": self.employee,
                "from_date": self.start_date,
                "to_date": self.end_date
            })[0][0])

            
        return total_tax_paid + tax_deducted_till_date + total_extra_tax + extra_current_tax_amount
    
    def calculate_variable_tax(self, tax_component):
        # print("Total  Piad Tax \n\n\n\n")
        self.previous_total_paid_taxes = self.get_tax_paid_in_period(
            self.payroll_period.start_date, self.start_date, tax_component
        )


        # Structured tax amount
        eval_locals, default_data = self.get_data_for_eval()
        self.total_structured_tax_amount = calculate_tax_by_tax_slab(
            self.total_taxable_earnings_without_full_tax_addl_components,
            self.tax_slab,
            self.whitelisted_globals,
            eval_locals,
        )

        self.current_structured_tax_amount = (
            self.total_structured_tax_amount - self.previous_total_paid_taxes
        ) / self.remaining_sub_periods

        # Total taxable earnings with additional earnings with full tax
        self.full_tax_on_additional_earnings = 0.0
        if self.current_additional_earnings_with_full_tax:
            self.total_tax_amount = calculate_tax_by_tax_slab(
                self.total_taxable_earnings, self.tax_slab, self.whitelisted_globals, eval_locals
            )
            self.full_tax_on_additional_earnings = self.total_tax_amount - self.total_structured_tax_amount

        current_tax_amount = self.current_structured_tax_amount + self.full_tax_on_additional_earnings
        if flt(current_tax_amount) < 0:
            current_tax_amount = 0

        self._component_based_variable_tax[tax_component].update(
            {
                "previous_total_paid_taxes": self.previous_total_paid_taxes,
                "total_structured_tax_amount": self.total_structured_tax_amount,
                "current_structured_tax_amount": self.current_structured_tax_amount,
                "full_tax_on_additional_earnings": self.full_tax_on_additional_earnings,
                "current_tax_amount": current_tax_amount,
            }
        )

        # Minus the amount from monthly tax that is already paid to tax authorities
        extra_current_tax_amount = 0
        if frappe.db.exists("DocType", "Paid Income Tax Monthly"):
            extra_current_tax_amount = flt(frappe.db.sql("""
                select 
                    sum(pitm.amount) 
                from 
                    `tabPaid Income Tax Monthly` pitm
                where
                    pitm.docstatus=1
                    and %(from_date)s>=pitm.period_from
                    and  %(to_date)s<=pitm.period_to
                    and %(from_date)s<=pitm.payroll_date
                    and  %(to_date)s>=pitm.payroll_date
                    and pitm.employee=%(employee)s
            """,{
                "employee": self.employee,
                "from_date": self.start_date,
                "to_date": self.end_date
            })[0][0])

        return current_tax_amount - extra_current_tax_amount

    def get_taxable_earnings_for_prev_period(self, start_date, end_date, allow_tax_exemption=False):
	    

        exempted_amount = 0
        taxable_earnings = self.get_salary_slip_details(
            start_date, end_date, parentfield="earnings", is_tax_applicable=1
        )

        if allow_tax_exemption:
            exempted_amount = self.get_salary_slip_details(
                start_date, end_date, parentfield="deductions", exempted_from_income_tax=1
            )

        opening_taxable_earning = self.get_opening_for("taxable_earnings_till_date", start_date, end_date)

        # Plus the amount earned before in the same payroll period
        prev_taxable_amount = 0
        if frappe.db.exists("DocType", "Previous Taxable Income"):
            prev_taxable_amount = flt(frappe.db.sql("""
                select 
                    sum(pti.amount) 
                from 
                    `tabPrevious Taxable Income` pti
                where
                    pti.docstatus=1
                    and %(from_date)s>=pti.period_from
                    and  %(to_date)s<=pti.period_to
                    and pti.employee=%(employee)s
            """,{
                "employee": self.employee,
                "from_date": self.start_date,
                "to_date": self.end_date
            })[0][0])


        return (taxable_earnings + opening_taxable_earning + prev_taxable_amount) - exempted_amount, exempted_amount

    # def before_save(self) :
        
    #     if self.custom_adjust_negative_salary == 1 and self.custom_check_adjustment == 1 and self.net_pay < 0 :
    #         create_salary_adjustment_for_negative_salary(self.name)
        
    #     elif self.net_pay < 0 :
    #         self.custom_adjust_negative_salary = 0


    #     fund_contribution = frappe.get_list(
    #             "Fund Contribution",
    #             filters={
    #                 "employee": self.employee
    #             },
    #             fields=["*"],
                
    #         )
    #     if fund_contribution:
    #         contribution_doc = frappe.get_doc("Fund Contribution", fund_contribution[0])
    #         fund_setting_name = contribution_doc.fund_setting
    #         fund_setting = frappe.get_doc("Fund Setting", fund_setting_name)

    #         if fund_setting.calculation_type == "Fixed":
    #             if fund_setting.fund_component and fund_setting.own_value:
    #                 self.deductions = [
    #                         row for row in self.deductions
    #                         if row.salary_component != fund_setting.fund_component
    #                     ]
    #                 row1 = {"salary_component": fund_setting.fund_component , "amount" : fund_setting.own_value, "year_to_date" : fund_setting.own_value }
    #                 self.append("deductions", row1)
                    

    #             if fund_setting.company_fund_component and fund_setting.company_value:
    #                 self.earnings = [
    #                         row for row in self.earnings
    #                         if row.salary_component != fund_setting.company_fund_component
    #                     ]
    #                 row2 = {"salary_component": fund_setting.company_fund_component , "amount" : fund_setting.company_value, "year_to_date" : fund_setting.company_value }
    #                 self.append("earnings", row2)
    #                 contribution_doc.fund_contribution_entry = []
    #                 contribution_doc.append("fund_contribution_entry", {
    #                     "contribution_type": "Company",
    #                     "amount": fund_setting.company_value,
    #                     "date": self.posting_date
    #                 })
    #                 contribution_doc.save()

            
    #         elif fund_setting.calculation_type == "% of Payment":

    #             earnings_dict = {earning.salary_component: earning.amount for earning in self.earnings}
    #             if fund_setting.dependent_components:
    #                 total_fund_amount = 0

    #                 for component in fund_setting.dependent_components:
    #                     if component.component in earnings_dict:
    #                         earnings_amount = earnings_dict[component.component]
    #                         calculated_amount = round((earnings_amount * component.percent) / 100, 2)
    #                         total_fund_amount += calculated_amount

    #                 self.deductions = [
    #                     row for row in self.deductions
    #                     if row.salary_component not in [fund_setting.fund_component]
    #                 ]

    #                 if total_fund_amount > 0:
    #                     self.append("deductions", {
    #                         "salary_component": fund_setting.fund_component,
    #                         "amount": total_fund_amount,
    #                         "year_to_date": total_fund_amount
    #                     })

    #             if fund_setting.company_dependent_components:
    #                 total_fund_amount = 0

    #                 for component in fund_setting.company_dependent_components:
    #                     if component.component in earnings_dict:
    #                         earnings_amount = earnings_dict[component.component]
    #                         calculated_amount = round((earnings_amount * component.percent) / 100, 2)
    #                         total_fund_amount += calculated_amount

    #                 self.earnings = [
    #                     row for row in self.earnings
    #                     if row.salary_component not in [fund_setting.company_fund_component]
    #                 ]

    #                 if total_fund_amount > 0:
    #                     self.append("earnings", {
    #                         "salary_component": fund_setting.company_fund_component,
    #                         "amount": total_fund_amount,
    #                         "year_to_date": total_fund_amount
    #                     })
                    
    #                 contribution_doc.fund_contribution_entry = []
    #                 contribution_doc.append("fund_contribution_entry", {
    #                     "contribution_type": "Company",
    #                     "amount": total_fund_amount,
    #                     "date": self.posting_date
    #                 })
    #                 contribution_doc.save()
    #             else:
    #                 self.earnings = [
    #                     row for row in self.earnings
    #                     if row.salary_component not in [fund_setting.company_fund_component]
    #                 ]

    #         elif fund_setting.calculation_type == "% of Rate":
    #             salary_structure = frappe.get_doc("Salary Structure", self.salary_structure)
    #             earnings_dict1 = {
    #                 earning.salary_component: earning.formula
    #                 for earning in salary_structure.get("earnings")
    #             }
    #             salary_structure_assignment = frappe.db.sql("""
    #                 SELECT base 
    #                 FROM `tabSalary Structure Assignment`
    #                 WHERE salary_structure = %s
    #                 AND from_date BETWEEN %s AND %s
    #                 ORDER BY from_date DESC
    #                 LIMIT 1
    #             """, (self.salary_structure, self.start_date, self.end_date), as_dict=True)
    #             base_value = salary_structure_assignment[0].base if salary_structure_assignment else 0
    #             total_fund_amount1 = 0

    #             if fund_setting.dependent_components:
    #                 for component in fund_setting.dependent_components:
                        
    #                     if component.component in earnings_dict1:
    #                         formula = earnings_dict1[component.component]
    #                         earnings_amount = frappe.safe_eval(formula, {}, {"custom_base": base_value})
    #                         calculated_amount = round((earnings_amount * component.percent) / 100, 2)
    #                         total_fund_amount1 = total_fund_amount1 + calculated_amount
    #                 self.deductions = [
    #                     row for row in self.deductions
    #                     if row.salary_component not in [fund_setting.fund_component]
    #                 ]
    #                 if total_fund_amount1 > 0:
    #                     self.append("deductions", {
    #                         "salary_component": fund_setting.fund_component,
    #                         "amount": total_fund_amount1,
    #                         "year_to_date": total_fund_amount1
    #                     })
    #             total_fund_amount2 = 0
    #             if fund_setting.company_dependent_components:
    #                 for component in fund_setting.company_dependent_components:
                        
    #                     if component.component in earnings_dict1:
    #                         formula = earnings_dict1[component.component]
    #                         earnings_amount = frappe.safe_eval(formula, {}, {"custom_base": base_value})
    #                         calculated_amount = round((earnings_amount * component.percent) / 100, 2)
    #                         total_fund_amount2 = total_fund_amount2 + calculated_amount
    #                 self.earnings = [
    #                     row for row in self.earnings
    #                     if row.salary_component not in [fund_setting.company_fund_component]
    #                 ]
    #                 if total_fund_amount2 > 0:
    #                     self.append("earnings", {
    #                         "salary_component": fund_setting.company_fund_component,
    #                         "amount": total_fund_amount2,
    #                         "year_to_date": total_fund_amount2
    #                     })
            
    #                 contribution_doc.fund_contribution_entry = []
    #                 contribution_doc.append("fund_contribution_entry", {
    #                     "contribution_type": "Company",
    #                     "amount": total_fund_amount2,
    #                     "date": self.posting_date
    #                 })
    #                 contribution_doc.save()

        # self.custom_check_adjustment = 0
        # self.calculate_net_pay()
        # self.compute_year_to_date()
        # self.compute_month_to_date()
        # self.compute_component_wise_year_to_date()





