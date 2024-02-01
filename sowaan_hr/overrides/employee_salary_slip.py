import frappe
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip

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