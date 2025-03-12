import frappe  # For interacting with the database and Frappe framework utilities
from frappe.query_builder import DocType  # For query building
from frappe.utils import flt  # For float conversion with precision handling
from frappe import _
import erpnext
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
	get_accounting_dimensions,
)
from hrms.payroll.doctype.salary_slip.salary_slip_loan_utils import if_lending_app_installed
from hrms.payroll.doctype.payroll_entry.payroll_entry import PayrollEntry, get_existing_salary_slips, log_payroll_failure
from hrms.payroll.doctype.salary_withholding.salary_withholding import link_bank_entry_in_salary_withholdings

class OverridePayrollEntry(PayrollEntry):

    @frappe.whitelist()
    def create_salary_slips(self):
        """
        Creates salary slip for selected employees if already not created
        """
        print("from override 20 ************")
        self.check_permission("write")
        employees = [emp.employee for emp in self.employees]

        if employees:
            args = frappe._dict(
                {
                    "salary_slip_based_on_timesheet": self.salary_slip_based_on_timesheet,
                    "payroll_frequency": self.payroll_frequency,
                    "start_date": self.start_date,
                    "end_date": self.end_date,
                    "company": self.company,
                    "posting_date": self.posting_date,
                    "deduct_tax_for_unclaimed_employee_benefits": self.deduct_tax_for_unclaimed_employee_benefits,
                    "deduct_tax_for_unsubmitted_tax_exemption_proof": self.deduct_tax_for_unsubmitted_tax_exemption_proof,
                    "payroll_entry": self.name,
                    "exchange_rate": self.exchange_rate,
                    "currency": self.currency,
                }
            )
            if len(employees) > 30 or frappe.flags.enqueue_payroll_entry:
                self.db_set("status", "Queued")
                frappe.enqueue(
                    create_salary_slips_for_employees,
                    timeout=3000,
                    employees=employees,
                    args=args,
                    publish_progress=False,
                )
                frappe.msgprint(
                    _("Salary Slip creation is queued. It may take a few minutes"),
                    alert=True,
                    indicator="blue",
                )
            else:
                create_salary_slips_for_employees(employees, args, publish_progress=False)
                # since this method is called via frm.call this doc needs to be updated manually
                self.reload()

    @frappe.whitelist()
    def has_bank_entries(self) -> dict[str, bool]:
        je = frappe.qb.DocType("Journal Entry")
        jea = frappe.qb.DocType("Journal Entry Account")

        bank_entries = (
            frappe.qb.from_(je)
            .inner_join(jea)
            .on(je.name == jea.parent)
            .select(je.name)
            .where(
                (je.voucher_type == "Bank Entry")
                & (jea.reference_name == self.name)
                & (jea.reference_type == "Payroll Entry")
            )
        ).run(as_dict=True)

        if bool(bank_entries):
            bank_entries = not any(employee.custom_payable > employee.custom_pay for employee in self.employees if employee.is_salary_withheld == 0)
        print(bank_entries, "checking bacnk Entry ******")
        return {
            "has_bank_entries": bool(bank_entries),
            "has_bank_entries_for_withheld_salaries": not any(
                employee.is_salary_withheld for employee in self.employees
            ),
        }
    
    @frappe.whitelist()
    def make_bank_entry(self, for_withheld_salaries=False):
        je = frappe.qb.DocType("Journal Entry")
        jea = frappe.qb.DocType("Journal Entry Account")

        bank_entries = (
            frappe.qb.from_(je)
            .inner_join(jea)
            .on(je.name == jea.parent)
            .select(je.name)
            .where(
                (je.voucher_type == "Bank Entry")
                & (jea.reference_name == self.name)
                & (jea.reference_type == "Payroll Entry")
            )
        ).run(as_dict=True)


        self.check_permission("write")
        self.employee_based_payroll_payable_entries = {}
        employee_wise_accounting_enabled = frappe.db.get_single_value(
            "Payroll Settings", "process_payroll_accounting_entry_based_on_employee"
        )

        salary_slip_total = 0
        salary_details = self.get_salary_slip_details(for_withheld_salaries)
        for salary_detail in salary_details:
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
                            self.set_employee_based_payroll_payable_entries(
                                "earnings",
                                salary_detail.employee,
                                salary_detail.amount,
                                salary_detail.salary_structure,
                            )
                        salary_slip_total += salary_detail.amount

            if salary_detail.parentfield == "deductions":
                statistical_component = frappe.db.get_value(
                    "Salary Component", salary_detail.salary_component, "statistical_component", cache=True
                )

                if not statistical_component:
                    if employee_wise_accounting_enabled:
                        self.set_employee_based_payroll_payable_entries(
                            "deductions",
                            salary_detail.employee,
                            salary_detail.amount,
                            salary_detail.salary_structure,
                        )

                    salary_slip_total -= salary_detail.amount

        total_loan_repayment = self.process_loan_repayments_for_bank_entry(salary_details) or 0
        salary_slip_total -= total_loan_repayment

        bank_entry = None
        if not bool(bank_entries):
            if salary_slip_total > 0:
                remark = "withheld salaries" if for_withheld_salaries else "salaries"
                bank_entry = self.set_accounting_entries_for_bank_entry(salary_slip_total, remark)

                if for_withheld_salaries:
                    link_bank_entry_in_salary_withholdings(salary_details, bank_entry.name)
        else:
            for emp in self.employees:
                if emp.is_salary_withheld == 0:
                    salary_slip_total = emp.custom_payable - emp.custom_pay
                    if salary_slip_total > 0:
                        remark = "salaries"
                        bank_entry = self.set_accounting_entries_for_bank_entry_partial(salary_slip_total, remark)
                        print(emp.employee, "Hello")
        return bank_entry
       

    @frappe.whitelist()
    def released_salary(self, employees, for_withheld_salaries=False):
        self.check_permission("write")
        self.employee_based_payroll_payable_entries = {}
        employee_wise_accounting_enabled = frappe.db.get_single_value(
            "Payroll Settings", "process_payroll_accounting_entry_based_on_employee"
        )

        # released_entries = self.get_employee_released_bank_entry(employees)
        # released_parties = {entry['party'] for entry in released_entries}

        # # Remove employees that are in released_parties
        # filtered_employees = [emp for emp in employees if emp not in released_parties]
        # print(filtered_employees, "print ******************")
        

        salary_slip_total = 0
        salary_details = self.get_employee_salary_slip_details(employees, for_withheld_salaries)
        for salary_detail in salary_details:
            # for je in released_entries:
            #     if salary_detail.employee == je.party:
            #         print(salary_detail, "Move forword***** \n\n")
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
                            self.set_employee_based_payroll_payable_entries(
                                "earnings",
                                salary_detail.employee,
                                salary_detail.amount,
                                salary_detail.salary_structure,
                            )
                        salary_slip_total += salary_detail.amount

            if salary_detail.parentfield == "deductions":
                statistical_component = frappe.db.get_value(
                    "Salary Component", salary_detail.salary_component, "statistical_component", cache=True
                )

                if not statistical_component:
                    if employee_wise_accounting_enabled:
                        self.set_employee_based_payroll_payable_entries(
                            "deductions",
                            salary_detail.employee,
                            salary_detail.amount,
                            salary_detail.salary_structure,
                        )

                    salary_slip_total -= salary_detail.amount

        total_loan_repayment = self.process_loan_repayments_for_bank_entry(salary_details) or 0
        salary_slip_total -= total_loan_repayment
        bank_entry = None
        if salary_slip_total > 0:
            remark = "withheld salaries" if for_withheld_salaries else "salaries"
            bank_entry = self.set_accounting_entries_for_bank_entry(salary_slip_total, remark)

            if for_withheld_salaries:
                link_bank_entry_in_salary_withholdings(salary_details, bank_entry.name)

        return bank_entry
    
    @frappe.whitelist()
    def get_employee_released_bank_entry(self, employees):
        JournalEntry = frappe.qb.DocType("Journal Entry")
        JournalEntryAccount = frappe.qb.DocType("Journal Entry Account")

        query = (
            frappe.qb.from_(JournalEntry)
            .join(JournalEntryAccount)
            .on(JournalEntry.name == JournalEntryAccount.parent)
            .select(
                JournalEntry.name,
                JournalEntryAccount.account,
                JournalEntryAccount.party,
                JournalEntryAccount.debit_in_account_currency
            ).where(
                (JournalEntry.docstatus == 1) &
                (JournalEntryAccount.party_type == "Employee") &
                (JournalEntryAccount.party.isin(employees))
            )
        )

        return query.run(as_dict=True)

    def get_employee_salary_slip_details(self, employees, for_withheld_salaries=False):
        SalarySlip = frappe.qb.DocType("Salary Slip")
        SalaryDetail = frappe.qb.DocType("Salary Detail")

        query = (
            frappe.qb.from_(SalarySlip)
            .join(SalaryDetail)
            .on(SalarySlip.name == SalaryDetail.parent)
            .select(
                SalarySlip.name,
                SalarySlip.employee,
                SalarySlip.salary_structure,
                SalarySlip.salary_withholding_cycle,
                SalaryDetail.salary_component,
                SalaryDetail.amount,
                SalaryDetail.parentfield,
            )
            .where(
                (SalarySlip.docstatus == 1)
                & (SalarySlip.start_date >= self.start_date)
                & (SalarySlip.end_date <= self.end_date)
                & (SalarySlip.payroll_entry == self.name)
                & (SalarySlip.employee.isin(employees))
            )
        )

        if "lending" in frappe.get_installed_apps():
            query = query.select(SalarySlip.total_loan_repayment)
        if for_withheld_salaries:
            query = query.where(SalarySlip.status == "Withheld")
        else:
            query = query.where(SalarySlip.status != "Withheld")
        return query.run(as_dict=True)

    def set_accounting_entries_for_bank_entry_partial(self, je_payment_amount, user_remark):
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
                for emp in self.employees:
                    if emp.custom_payable > emp.custom_pay and employee == emp.employee:
                        je_payment_amount = (
                            (employee_details.get("earnings", 0) or 0)
                            - (employee_details.get("deductions", 0) or 0)
                            - (employee_details.get("total_loan_repayment", 0) or 0) - emp.custom_pay
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

        return self.make_journal_entry(
            accounts,
            currencies,
            voucher_type="Bank Entry",
            user_remark=_("Payment of {0} from {1} to {2}").format(
                _(user_remark), self.start_date, self.end_date
            ),
        )

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
                je_payment_amount = (
                    (employee_details.get("earnings", 0) or 0)
                    - (employee_details.get("deductions", 0) or 0)
                    - (employee_details.get("total_loan_repayment", 0) or 0)
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

        return self.make_journal_entry(
            accounts,
            currencies,
            voucher_type="Bank Entry",
            user_remark=_("Payment of {0} from {1} to {2}").format(
                _(user_remark), self.start_date, self.end_date
            ),
        )

    def update_accounting_dimensions(self, row, accounting_dimensions):
        for dimension in accounting_dimensions:
            row.update({dimension: self.get(dimension)})

        return row

    def set_employee_based_payroll_payable_entries(
		self, component_type, employee, amount, salary_structure=None
	):
        employee_details = self.employee_based_payroll_payable_entries.setdefault(employee, {})

        employee_details.setdefault(component_type, 0)
        employee_details[component_type] += amount

        if salary_structure and "salary_structure" not in employee_details:
            employee_details["salary_structure"] = salary_structure

    @if_lending_app_installed
    def process_loan_repayments_for_bank_entry(self, salary_details: list[dict]) -> float:
        unique_salary_slips = {row["employee"]: row for row in salary_details}.values()
        total_loan_repayment = sum(flt(slip.get("total_loan_repayment", 0)) for slip in unique_salary_slips)

        if self.employee_based_payroll_payable_entries:
            for salary_slip in unique_salary_slips:
                if salary_slip.get("total_loan_repayment"):
                    self.set_employee_based_payroll_payable_entries(
                        "total_loan_repayment",
                        salary_slip.employee,
                        salary_slip.total_loan_repayment,
                        salary_slip.salary_structure,
                    )

        return total_loan_repayment
    
    def get_amount_and_exchange_rate_for_journal_entry(self, account, amount, company_currency, currencies):
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
    
    def get_payroll_cost_centers_for_employee(self, employee, salary_structure):
        if not hasattr(self, "employee_cost_centers"):
            self.employee_cost_centers = {}

        if not self.employee_cost_centers.get(employee):
            SalaryStructureAssignment = frappe.qb.DocType("Salary Structure Assignment")
            EmployeeCostCenter = frappe.qb.DocType("Employee Cost Center")
            assignment_subquery = (
                frappe.qb.from_(SalaryStructureAssignment)
                .select(SalaryStructureAssignment.name)
                .where(
                    (SalaryStructureAssignment.employee == employee)
                    & (SalaryStructureAssignment.salary_structure == salary_structure)
                    & (SalaryStructureAssignment.docstatus == 1)
                    & (SalaryStructureAssignment.from_date <= self.end_date)
                )
                .orderby(SalaryStructureAssignment.from_date, order=frappe.qb.desc)
                .limit(1)
            )
            cost_centers = dict(
                (
                    frappe.qb.from_(EmployeeCostCenter)
                    .select(EmployeeCostCenter.cost_center, EmployeeCostCenter.percentage)
                    .where(EmployeeCostCenter.parent == assignment_subquery)
                ).run(as_list=True)
            )

            if not cost_centers:
                default_cost_center, department = frappe.get_cached_value(
                    "Employee", employee, ["payroll_cost_center", "department"]
                )

                if not default_cost_center and department:
                    default_cost_center = frappe.get_cached_value(
                        "Department", department, "payroll_cost_center"
                    )

                if not default_cost_center:
                    default_cost_center = self.cost_center

                cost_centers = {default_cost_center: 100}

            self.employee_cost_centers.setdefault(employee, cost_centers)

        return self.employee_cost_centers.get(employee, {})
    
    def make_journal_entry(
        self,
        accounts,
        currencies,
        payroll_payable_account=None,
        voucher_type="Journal Entry",
        user_remark="",
        submitted_salary_slips: list | None = None,
        submit_journal_entry=False,
    ) -> str:
        multi_currency = 0
        if len(currencies) > 1:
            multi_currency = 1

        journal_entry = frappe.new_doc("Journal Entry")
        journal_entry.voucher_type = voucher_type
        journal_entry.user_remark = user_remark
        journal_entry.company = self.company
        journal_entry.posting_date = self.posting_date
        journal_entry.custom_smart_posting_date = self.posting_date
        journal_entry.set("accounts", accounts)
        journal_entry.multi_currency = multi_currency

        if voucher_type == "Journal Entry":
            journal_entry.title = payroll_payable_account

        journal_entry.save(ignore_permissions=True)

        try:
            if submit_journal_entry:
                journal_entry.submit()

            if submitted_salary_slips:
                self.set_journal_entry_in_salary_slips(submitted_salary_slips, jv_name=journal_entry.name)

        except Exception as e:
            if type(e) in (str, list, tuple):
                frappe.msgprint(e)

            self.log_error("Journal Entry creation against Salary Slip failed")
            raise

        return journal_entry
    
    def set_journal_entry_in_salary_slips(self, submitted_salary_slips, jv_name=None):
        SalarySlip = frappe.qb.DocType("Salary Slip")
        (
            frappe.qb.update(SalarySlip)
            .set(SalarySlip.journal_entry, jv_name)
            .where(SalarySlip.name.isin([salary_slip.name for salary_slip in submitted_salary_slips]))
        ).run()


def create_salary_slips_for_employees(employees, args, publish_progress=True):
    payroll_entry = frappe.get_cached_doc("Payroll Entry", args.payroll_entry)

    try:
        salary_slips_exist_for = get_existing_salary_slips(employees, args)
        count = 0

        employees = list(set(employees) - set(salary_slips_exist_for))
        for emp in employees:
            args.update({"doctype": "Salary Slip", "employee": emp})
            salaryslip = frappe.get_doc(args).insert()
            for pyemp in payroll_entry.employees:
                frappe.db.set_value("Payroll Employee Detail", pyemp.name, "custom_payable", salaryslip.net_pay)

            count += 1
            if publish_progress:
                frappe.publish_progress(
                    count * 100 / len(employees),
                    title=_("Creating Salary Slips..."),
                )

        payroll_entry.db_set({"status": "Submitted", "salary_slips_created": 1, "error_message": ""})

        if salary_slips_exist_for:
            frappe.msgprint(
                _(
                    "Salary Slips already exist for employees {}, and will not be processed by this payroll."
                ).format(frappe.bold(", ".join(emp for emp in salary_slips_exist_for))),
                title=_("Message"),
                indicator="orange",
            )

    except Exception as e:
        frappe.db.rollback()
        log_payroll_failure("creation", payroll_entry, e)

    finally:
        frappe.db.commit()  # nosemgrep
        frappe.publish_realtime("completed_salary_slip_creation", user=frappe.session.user)
