from __future__ import unicode_literals
from datetime import date
import json
import itertools
from tabnanny import check
import frappe
from frappe.utils import (
    nowdate, flt, cstr, getdate, add_to_date, date_diff, cint
)
from frappe import _
from erpnext.payroll.doctype.payroll_entry.payroll_entry import get_end_date
from erpnext.hr.utils import get_holiday_dates_for_employee

@frappe.whitelist()
def get_payroll_date(employee):
    payroll_entries = frappe.db.get_all(
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
def get_attendance(employee, from_date, to_date, page):
    pageSize = 15
    page = int(page)
    
    if(page <= 0):
        return "Page should be greater or equal of 1"

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
        order_by="attendance_date desc",
        start=(page-1)*pageSize,
        page_length=pageSize,
    )
  
    return attendance

@frappe.whitelist()
def get_attendance_summary_statuswise(employee, from_date, to_date):
    filters = {
        "docstatus": 1,
        "attendance_date": ["between", (getdate(from_date), getdate(to_date))]
    }
    if(employee):
        filters["employee"] = employee

    att_list = frappe.db.get_list(
        "Attendance",
        filters=filters,
        fields=['status','attendance_date'],
        order_by="status desc",
    )
    att_group =  itertools.groupby(
			att_list, key=lambda x: x["status"]
		)
    
    result = []
    for key, group in att_group:
        result.append({"status":key,"count":len(list(group))})

    
    # get late entries
    filters["status"] = "Present"   
    filters["late_entry"] = 1
    filters["late_approved"] = 0   
    lates = len(frappe.db.get_list(
        "Attendance",
        filters=filters
    ))

    # get early departures
    filters["status"] = "Present" 
    filters["early_exit"] = 1   
    early = len(frappe.db.get_list(
        "Attendance",
        filters=filters
    ))

    # get holidays
    holidays = get_holiday_dates_for_employee(employee, from_date, to_date)
    holidays = len(list(filter(lambda x: getdate(x) < getdate(nowdate()), holidays)))
    
    result.append({"status":"Late","count":lates})
    result.append({"status":"Early","count":early})
    result.append({"status":"Holiday","count":holidays})

    return  result

# the below method (get_attendance_summary) is deprecated and will be removed in next major release, 
# please use (get_attendance_summary_statuswise) instead
@frappe.whitelist()
def get_attendance_summary(employee, from_date, to_date):
    filters = {
        "docstatus": 1,
        "attendance_date": ["between", (getdate(from_date), getdate(to_date))]
    }
    if(employee):
        filters["employee"] = employee

    filters["status"] = ["in",["Present","Half Day"]]
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
    filters["late_approved"] = 0   
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
    
@frappe.whitelist()
def get_monthly_hours(employee, from_date, to_date):

    payroll_based_on = frappe.db.get_value("Payroll Settings", None, "payroll_based_on")
    standard_working_hours = float(frappe.db.get_value("HR Settings", None, "standard_working_hours"))
    if standard_working_hours <= 0:
        return ""
    include_holidays_in_total_working_days = frappe.db.get_single_value(
        "Payroll Settings", "include_holidays_in_total_working_days"
    )

    holidays = get_holiday_dates_for_employee(employee, from_date, to_date)

    emp_slip = frappe.new_doc("Salary Slip")
    emp_slip.start_date = from_date
    emp_slip.end_date = to_date
    emp_slip.employee = employee

    emp_slip.get_working_days_details()

    required_hours = ((emp_slip.payment_days or 0)+(emp_slip.absent_days or 0)+(emp_slip.leave_without_pay or 0))*standard_working_hours

    att = frappe.get_all("Attendance", filters={
        "employee": ["=", employee],
        "docstatus": 1,
        "attendance_date": ["between", (getdate(from_date), getdate(to_date))],
    }, fields=['*'])

    provided_hours = sum(c.working_hours for c in att)
    if include_holidays_in_total_working_days:
        holidays_before_today = list(filter(lambda x: getdate(x) < getdate(nowdate()), holidays))
        provided_hours += len(holidays_before_today)*standard_working_hours
    
    for idx, x in enumerate(att): 
        if (x.status == "Half Day" or x.status == "On Leave") and x.leave_type != '' and x.leave_type != None:
            leave = frappe.get_doc("Leave Type", x.leave_type)
            if x.status == "Half Day" and leave and not leave.is_lwp:
                provided_hours += standard_working_hours * 0.5
            elif x.status == "On Leave" and leave and leave.is_ppl:
                provided_hours += standard_working_hours * (1-leave.fraction_of_daily_salary_per_leave)
            elif x.status == "On Leave" and leave and not leave.is_ppl and not leave.is_lwp:
                provided_hours += standard_working_hours
        
        if x.status == "Half Day" and x.working_hours == 0:
            daily_wages_fraction_for_half_day = float(frappe.db.get_value("Payroll Settings", None, "daily_wages_fraction_for_half_day"))
            if daily_wages_fraction_for_half_day:
                provided_hours += standard_working_hours * daily_wages_fraction_for_half_day

    less_hours = round(required_hours-provided_hours, 2)

    result = []
    result.append({"status":"Required Hours","count":round(required_hours,2), "isOk": True})
    result.append({"status":"Provided Hours","count":round(provided_hours,2), "isOk": True if less_hours<=0 else False})
    result.append({"status":"Less Hours","count":less_hours if less_hours > 0 else 0, "isOk": True if less_hours<=0 else False})

    return result