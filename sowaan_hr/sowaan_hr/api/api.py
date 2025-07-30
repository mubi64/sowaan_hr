import frappe
from bs4 import BeautifulSoup
from frappe import _
from frappe.utils import cstr

import json
from frappe.model.mapper import get_mapped_doc
from frappe.utils import nowdate, getdate, date_diff
from datetime import datetime
# from hrms.payroll.doctype.salary_slip.salary_slip import (calculate_net_pay, compute_year_to_date, compute_month_to_date, compute_component_wise_year_to_date)



def gen_response(status, message, data=[]):
    frappe.response["http_status_code"] = status
    if status == 500:
        frappe.response["message"] = BeautifulSoup(str(message)).get_text()
    else:
        frappe.response["message"] = message
    frappe.response["data"] = data


def sort_by_char_frequency(statuses):
    max_length = max(len(s['status']) for s in statuses)
    index_counts = [0] * max_length

    # Count characters at each index position
    for s in statuses:
        for i in range(len(s['status'])):
            index_counts[i] += 1

    # Sort by character counts at each index
    return sorted(statuses, key=lambda s: tuple(index_counts[i] for i in range(len(s['status']))))



@frappe.whitelist()
def get_emloyees(branch , department , employee) :
    
    values = {
        'branch' : branch ,
        'department' : department ,
        'employee' : employee ,
    }
    
    if employee :
        emp_list = frappe.db.sql("""
            SELECT
                emp.name ,
                emp.employee_name ,
                emp.department ,
                emp.branch ,
                emp.designation                                   
                                 
            FROM
                `tabEmployee` emp
            WHERE
                emp.name = %(employee)s
                AND emp.status = 'Active'                 
        """, values=values , as_dict=1)

    else :
        if branch and department :
            emp_list = frappe.db.sql("""
            SELECT
                emp.name ,
                emp.employee_name ,
                emp.department ,
                emp.branch ,
                emp.designation 
            FROM
                `tabEmployee` emp
            WHERE
                emp.branch = %(branch)s
                AND emp.department = %(department)s
                AND emp.status = 'Active'                                       
            """, values=values , as_dict=1)
            
        elif branch :
            emp_list = frappe.db.sql("""
            SELECT
                emp.name ,
                emp.employee_name ,
                emp.department ,
                emp.branch ,
                emp.designation                      
            FROM
                `tabEmployee` emp
            WHERE
                emp.branch = %(branch)s
                AND emp.status = 'Active'                                          
            """, values=values , as_dict=1)
        
        elif department :            
            emp_list = frappe.db.sql("""
            SELECT
                emp.name ,
                emp.employee_name ,
                emp.department ,
                emp.branch ,
                emp.designation 
            FROM
                `tabEmployee` emp
            WHERE
                emp.department = %(department)s
                AND emp.status = 'Active'                     
            """, values=values , as_dict=1)

        else :
            emp_list = frappe.db.sql("""
            SELECT
                emp.name ,
                emp.employee_name ,
                emp.department ,
                emp.branch ,
                emp.designation  
            FROM
                `tabEmployee` emp
            WHERE
                emp.status = 'Active'                                             
            """, values=values , as_dict=1)                     

    return emp_list





@frappe.whitelist()
def get_dates(from_date , frequency) :
    
    dates = []
    days = []
    date = from_date

    if frequency == 'Weekly' :
        for i in range(7) :
            dates.append(date)
            datetime_obj = frappe.utils.get_datetime(date)
            day = frappe.utils.get_weekday(datetime_obj)
            days.append(day)
            date = frappe.utils.add_days(date, 1)

    elif frequency == 'Bi Weekly' :
        for i in range(14) :
            dates.append(date)
            datetime_obj = frappe.utils.get_datetime(date)
            day = frappe.utils.get_weekday(datetime_obj)
            days.append(day)
            date = frappe.utils.add_days(date, 1)


    if frequency == 'Monthly' :        
        for i in range(28) :
            dates.append(date)
            datetime_obj = frappe.utils.get_datetime(date)
            day = frappe.utils.get_weekday(datetime_obj)
            days.append(day)
            date = frappe.utils.add_days(date, 1)


    return {"dates": dates, "days": days}     


@frappe.whitelist()
def create_salary_adjustment_for_negative_salary(doc_name) :

    ss_doc = frappe.get_doc("Salary Slip", doc_name)
    earn_comp = None
    ded_comp = None

    payroll_settings_doc = frappe.get_doc('SowaanHR Payroll Settings')

    for earn in payroll_settings_doc.earning :
        if earn.company == ss_doc.company :
            earn_comp = earn.component
            break

    for ded in payroll_settings_doc.deduction :
        if ded.company == ss_doc.company :
            ded_comp = ded.component
            break

    if earn_comp and not ded_comp :
        frappe.throw(f'Deduction Component is not set for {ss_doc.company}.')  
        
    elif ded_comp and not earn_comp :
        frappe.throw(f'Earning Component is not set for {ss_doc.company}.')

    elif not earn_comp and not ded_comp :
        frappe.throw(f'Earning and Deduction Components are not set for {ss_doc.company}.')

    else :    
        frappe.get_doc(dict(
            doctype = 'Additional Salary',
            employee = ss_doc.employee ,
            company = ss_doc.company ,
            payroll_date = ss_doc.end_date ,
            salary_component = earn_comp ,
            amount = -(ss_doc.net_pay - 1) ,
            docstatus = 1
        )).insert()
        
        day_after_end_date = frappe.utils.add_days(ss_doc.end_date, 1)

        frappe.get_doc(dict(
            doctype = 'Additional Salary',
            employee = ss_doc.employee ,
            company = ss_doc.company ,
            payroll_date = day_after_end_date ,
            salary_component = ded_comp ,
            amount = -(ss_doc.net_pay - 1) ,
            docstatus = 1
        )).insert()


@frappe.whitelist()
def send_password_expiry_alerts():
    # Get users with password expiry enabled
    users = frappe.get_all("User", filters={"enabled": 1, "user_type": "System User"}, fields=["name", "last_password_reset_date"])
    
    expiry_days = frappe.db.get_single_value("System Settings", "force_user_to_reset_password")
    if expiry_days > 0:
        for user in users:
            if not user.last_password_reset_date:
                continue
            days_since_reset = date_diff(getdate(nowdate()), user.last_password_reset_date)
            days_left = expiry_days - days_since_reset

            if days_left in [7, 3]:  # send alerts at 7 and 3 days before expiry
                subject = f"Your ERPNext password will expire in {days_left} day(s)"
                message = f"Dear {user.name},\n\nYour ERPNext password will expire in {days_left} day(s). Please change it from your account settings to avoid login issues.\n\nThanks."
                frappe.sendmail(recipients=[user.name], subject=subject, message=message)       
          





    

    








   




