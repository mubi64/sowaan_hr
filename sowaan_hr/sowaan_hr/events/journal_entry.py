import frappe

# after submit netpay update on payroll entry if payroll entry exist
def after_submit(self, method):
    print("Event Submittion *****")
    for acc in self.accounts:
        if acc.reference_type == "Payroll Entry" and acc.party_type == "Employee":
            if acc.debit_in_account_currency > 0:
                frappe.db.sql(
                    """
                    UPDATE `tabPayroll Employee Detail`
                    SET custom_pay = COALESCE(custom_pay, 0) + %s
                    WHERE parent = %s and employee = %s
                    """,
                    (acc.debit_in_account_currency, acc.reference_name, acc.party),
                )

# on cancel netpay update on payroll entry if payroll entry exist
def on_cancel(self, method):
    print("Event Cancel *****")
    for acc in self.accounts:
        if acc.reference_type == "Payroll Entry" and acc.party_type == "Employee":
            if acc.debit_in_account_currency > 0:
                frappe.db.sql(
                    """
                    UPDATE `tabPayroll Employee Detail`
                    SET custom_pay = COALESCE(custom_pay, 0) - %s
                    WHERE parent = %s and employee = %s
                    """,
                    (acc.debit_in_account_currency, acc.reference_name, acc.party),
                )