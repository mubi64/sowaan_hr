from __future__ import unicode_literals
from datetime import date
import json
from tabnanny import check
import frappe
from frappe.utils import nowdate, flt, cstr, getdate, add_to_date
from frappe import _
from erpnext.payroll.doctype.payroll_entry.payroll_entry import get_end_date

@frappe.whitelist()
def get_payroll_date(employee):
    payroll_entries = frappe.db.get_list(
        "Payroll Entry",
        filters=[
            ['docstatus', '=', 1,],
            ['Payroll Employee Detail', 'employee', '=', employee]],
        fields=["start_date","end_date","payroll_frequency"]
    )
    data = {}
    today = getdate(nowdate())
    if len(payroll_entries) > 0:
        payroll_entry = payroll_entries[0]

        pay_start = getdate(payroll_entry["start_date"])
        start_date = getdate(str(today.year)+'-'+str(today.month)+'-'+str(pay_start.day))
        if(start_date > today):
            start_date = add_to_date(start_date, months=-1)

        end_date = get_end_date(frequency=payroll_entry['payroll_frequency'], start_date=start_date)
        data["start_date"] = start_date
        data["end_date"] = end_date["end_date"]
    else:
        data["start_date"] = today.replace(day=1)
        data["end_date"] = today

    return data

@frappe.whitelist()
def get_attendance(employee, from_date, to_date):
    filters = {
        "docstatus": 1,
        "attendance_date": ["between", (getdate(from_date), getdate(to_date))]
    }
    if(employee):
        filters["employee"] = employee
    
    attendance = frappe.db.get_list(
        "Attendance",
        filters=filters,
        fields=["name","employee","employee_name","working_hours","status","attendance_date","in_time","out_time","late_entry","early_exit"],
        order_by="attendance_date desc"
    )
  
    return attendance

@frappe.whitelist()
def get_attendance_summary(employee, from_date, to_date):
    filters = {
        "docstatus": 1,
        "attendance_date": ["between", (getdate(from_date), getdate(to_date))]
    }
    if(employee):
        filters["employee"] = employee

    filters["status"] = "Present"   
    presents = len(frappe.db.get_list(
        "Attendance",
        filters=filters
    ))

    filters["status"] = "Absent"   
    absents = len(frappe.db.get_list(
        "Attendance",
        filters=filters

    ))

    filters["status"] = "Present"   
    filters["late_entry"] = 1   
    lates = len(frappe.db.get_list(
        "Attendance",
        filters=filters
    ))

    filters["status"] = "Present" 
    filters["early_exit"] = 1   
    early = len(frappe.db.get_list(
        "Attendance",
        filters=filters
    ))
    
    return {
        "presents":presents,
        "absents":absents,
        "lates":lates,
        "early":early
    }