import frappe
from frappe import _
from frappe.utils import  get_link_to_form
from hrms.payroll.doctype.additional_salary.additional_salary import AdditionalSalary




class EmployeeAdditionalSalary(AdditionalSalary):
    def validate_duplicate_additional_salary(self):
        if not self.overwrite_salary_structure_amount:
            return

        existing_additional_salary = frappe.db.exists(
            "Additional Salary",
            {
                "name": ["!=", self.name],
                "salary_component": self.salary_component,
                "payroll_date": self.payroll_date,
                "overwrite_salary_structure_amount": 1,
                "employee": self.employee,
                "docstatus": 1,
                "disabled": 0,
            },
        )

        if existing_additional_salary:
            msg = _(
                "Additional Salary for this salary component with {0} enabled already exists for this date"
            ).format(frappe.bold(_("Overwrite Salary Structure Amount")))
            msg += "<br><br>"
            msg += _("Reference: {0}").format(
                get_link_to_form("Additional Salary", existing_additional_salary)
            )
            frappe.throw(msg, title=_("Duplicate Overwritten Salary"))
