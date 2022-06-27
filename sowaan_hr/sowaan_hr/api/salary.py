from __future__ import unicode_literals
import json
import frappe
from frappe.utils import nowdate, flt, cstr
from frappe import _

@frappe.whitelist()
def get_salary_months(employee):
    months = frappe.db.get_list(
        "Salary Slip",
        filters={
            "employee":employee,
        },
        fields=["name","start_date","end_date"],
        order_by="end_date desc",
    )

    return months

@frappe.whitelist()
def get_salary_slip(salary_slip):
    slip = frappe.get_doc(
        "Salary Slip",
        salary_slip
    )

    return slip