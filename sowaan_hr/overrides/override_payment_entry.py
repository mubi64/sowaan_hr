import frappe  # For interacting with the database and Frappe framework utilities
from frappe.query_builder import DocType  # For query building
from frappe.utils import flt  # For float conversion with precision handling
from frappe import _
from hrms.payroll.doctype.payroll_entry.payroll_entry import PayrollEntry
import erpnext
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_accounting_dimensions,
)

class OverridePayrollEntry(PayrollEntry):
    @frappe.whitelist()
    def make_bank_entry(self):
        self.check_permission("write")
        self.employee_based_payroll_payable_entries = {}
        employee_wise_accounting_enabled = frappe.db.get_single_value(
            "Payroll Settings", "process_payroll_accounting_entry_based_on_employee"
        )
        salary_slip_total = 0
        employee_wise_loan_details = {}  # Track loans per employee
        salary_slips = self.get_salary_slip_details()

        # First pass: Calculate totals and track loans per employee
        for salary_detail in salary_slips:
            employee = salary_detail.employee
            if employee not in employee_wise_loan_details:
                employee_wise_loan_details[employee] = {
                    'earnings': 0,
                    'deductions': 0,
                    'loan_amount': 0,
                    'loan_processed': False
                }
            
            if salary_detail.parentfield == "earnings":
                (
                    is_flexible_benefit,
                    only_tax_impact,
                    create_separate_je,
                    statistical_component,
                ) = frappe.db.get_value(
                    "Salary Component",
                    salary_detail.salary_component,
                    (
                        "is_flexible_benefit",
                        "only_tax_impact",
                        "create_separate_payment_entry_against_benefit_claim",
                        "statistical_component",
                    ),
                    cache=True,
                )
                if only_tax_impact != 1 and statistical_component != 1:
                    if is_flexible_benefit == 1 and create_separate_je == 1:
                        self.set_accounting_entries_for_bank_entry(
                            salary_detail.amount, salary_detail.salary_component
                        )
                    else:
                        if employee_wise_accounting_enabled:
                            employee_wise_loan_details[employee]['earnings'] += salary_detail.amount
                        else:
                            salary_slip_total += salary_detail.amount
            
            elif salary_detail.parentfield == "deductions":
                statistical_component = frappe.db.get_value(
                    "Salary Component", salary_detail.salary_component, "statistical_component", cache=True
                )
                if not statistical_component:
                    if employee_wise_accounting_enabled:
                        employee_wise_loan_details[employee]['deductions'] += salary_detail.amount
                    else:
                        salary_slip_total -= salary_detail.amount
                        
            

            if (hasattr(salary_detail, 'total_loan_repayment') and 
            salary_detail.total_loan_repayment and 
            not employee_wise_loan_details[employee]['loan_processed']):


                employee_wise_loan_details[employee]['loan_amount'] += salary_detail.total_loan_repayment
                employee_wise_loan_details[employee]['loan_processed'] = True
                if not employee_wise_accounting_enabled:
                    salary_slip_total -= salary_detail.total_loan_repayment

        # Second pass: Create accounting entries
        if employee_wise_accounting_enabled:
            total_net_pay = 0
            for employee, details in employee_wise_loan_details.items():
                net_pay = details['earnings'] - details['deductions'] - details['loan_amount']
                total_net_pay += net_pay
                self.set_employee_based_payroll_payable_entries(
                    "earnings",
                    employee,
                    net_pay,
                    None  # salary structure is not needed here
                )
            # Set the company entry only once with the total
            self.set_accounting_entries_for_bank_entry(total_net_pay, "salary")
        else:
            # Set the company entry only once with the calculated total
            if salary_slip_total > 0:
                self.set_accounting_entries_for_bank_entry(salary_slip_total, "salary")

    def get_salary_slip_details(self):
        SalarySlip = frappe.qb.DocType("Salary Slip")
        SalaryDetail = frappe.qb.DocType("Salary Detail")
        # Check if the field exists before selecting
        select_fields = [
            SalarySlip.name, 
            SalarySlip.employee, 
            SalarySlip.salary_structure,
            
            SalaryDetail.salary_component, 
            SalaryDetail.amount, 
            SalaryDetail.parentfield
        ]
        
        

        if frappe.get_meta("Salary Slip").get_field("total_loan_repayment"):
            print("appended")
            select_fields.append(SalarySlip.total_loan_repayment)

     

        return (
            frappe.qb.from_(SalarySlip)
            .join(SalaryDetail)
            .on(SalarySlip.name == SalaryDetail.parent)
            .select(*select_fields)
            .where(
                (SalarySlip.docstatus == 1) & 
                (SalarySlip.start_date >= self.start_date) & 
                (SalarySlip.end_date <= self.end_date) & 
                (SalarySlip.payroll_entry == self.name)
            )
        ).run(as_dict=True)


    
    def set_accounting_entries_for_bank_entry(self, je_payment_amount, user_remark):
        payroll_payable_account = self.payroll_payable_account
        precision = frappe.get_precision("Journal Entry Account", "debit_in_account_currency")

        accounts = []
        currencies = []
        company_currency = erpnext.get_company_currency(self.company)
        accounting_dimensions = get_accounting_dimensions() or []

        exchange_rate, amount = self.get_amount_and_exchange_rate_for_journal_entry(
            self.payment_account, je_payment_amount, company_currency, currencies
        )
        accounts.append(
            self.update_accounting_dimensions(
                {
                    "account": self.payment_account,
                    "bank_account": self.bank_account,
                    "credit_in_account_currency": flt(amount, precision),
                    "exchange_rate": flt(exchange_rate),
                    "cost_center": self.cost_center,
                },
                accounting_dimensions,
            )
        )

        if self.employee_based_payroll_payable_entries:
            for employee, employee_details in self.employee_based_payroll_payable_entries.items():
                je_payment_amount = employee_details.get("earnings") - (
                    employee_details.get("deductions") or 0
                )
                exchange_rate, amount = self.get_amount_and_exchange_rate_for_journal_entry(
                    self.payment_account, je_payment_amount, company_currency, currencies
                )

                cost_centers = self.get_payroll_cost_centers_for_employee(
                    employee, employee_details.get("salary_structure")
                )

                for cost_center, percentage in cost_centers.items():
                    amount_against_cost_center = flt(amount) * percentage / 100
                    accounts.append(
                        self.update_accounting_dimensions(
                            {
                                "account": payroll_payable_account,
                                "debit_in_account_currency": flt(amount_against_cost_center, precision),
                                "exchange_rate": flt(exchange_rate),
                                "reference_type": self.doctype,
                                "reference_name": self.name,
                                "party_type": "Employee",
                                "party": employee,
                                "cost_center": cost_center,
                            },
                            accounting_dimensions,
                        )
                    )
        else:
            exchange_rate, amount = self.get_amount_and_exchange_rate_for_journal_entry(
                payroll_payable_account, je_payment_amount, company_currency, currencies
            )
            accounts.append(
                self.update_accounting_dimensions(
                    {
                        "account": payroll_payable_account,
                        "debit_in_account_currency": flt(amount, precision),
                        "exchange_rate": flt(exchange_rate),
                        "reference_type": self.doctype,
                        "reference_name": self.name,
                        "cost_center": self.cost_center,
                    },
                    accounting_dimensions,
                )
            )

        self.make_journal_entry(
            accounts,
            currencies,
            voucher_type="Bank Entry",
            user_remark=_("Payment of {0} from {1} to {2}").format(
                user_remark, self.start_date, self.end_date
            ),
        )
    
    def set_employee_based_payroll_payable_entries(
            self, component_type, employee, amount, salary_structure=None
        ):
            employee_details = self.employee_based_payroll_payable_entries.setdefault(employee, {})

            employee_details.setdefault(component_type, 0)
            employee_details[component_type] += amount

            if salary_structure and "salary_structure" not in employee_details:
                employee_details["salary_structure"] = salary_structure

    def get_amount_and_exchange_rate_for_journal_entry(
		self, account, amount, company_currency, currencies
	):
            conversion_rate = 1
            exchange_rate = self.exchange_rate
            account_currency = frappe.db.get_value("Account", account, "account_currency")

            if account_currency not in currencies:
                currencies.append(account_currency)

            if account_currency == company_currency:
                conversion_rate = self.exchange_rate
                exchange_rate = 1

            amount = flt(amount) * flt(conversion_rate)

            return exchange_rate, amount
    def update_accounting_dimensions(self, row, accounting_dimensions):
            for dimension in accounting_dimensions:
                row.update({dimension: self.get(dimension)})

            return row
            
            
            
            