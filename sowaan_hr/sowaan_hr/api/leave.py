import frappe
from frappe.desk.form.load import getdoc , getdoctype
from frappe.utils import date_diff, now
from sowaan_hr.sowaan_hr.api.workflow import apply_actions
from sowaan_hr.sowaan_hr.api.employee import get_allowed_employees, get_current_emp, get_employee_info

@frappe.whitelist()
def get_leaves(employee, page):
    pageSize = 15
    page = int(page)

    if(page <= 0):
        return "Page should be greater or equal of 1"

    filters = {}

    allowed_employees = get_allowed_employees()
    
    if employee:
        if (len(allowed_employees) > 0 and employee in allowed_employees) or len(allowed_employees) == 0:
            filters["employee"] = employee
        else:
            filters["employee"] = get_current_emp()
    elif len(allowed_employees) > 0:
        filters["employee"] = ["in", allowed_employees]
    
    leaves = frappe.db.get_list(
        "Leave Application",
        filters=filters,
        fields=[
            "name", 
            "status", 
            "to_date",
            "from_date", 
            "half_day", 
            "leave_type", 
            "description", 
            "posting_date",
            "employee_name",
            "half_day_date", 
            "total_leave_days", 
            "leave_approver_name",
            "workflow_state"
        ],
        order_by="modified DESC",
        start=(page-1)*pageSize,
        page_length=pageSize
    )

    return leaves

@frappe.whitelist()
def get_permission(name):
    doctype = "Leave Application"
    getdoc(doctype, name)

@frappe.whitelist()
def create_leave(employee, from_date, to_date, leave_type, description, leave_approver, half_day = False, half_day_date = None):
    day = date_diff(to_date, from_date)
    if (day > 0 and half_day == True):
        if (half_day_date == None):
            raise Exception("Mandatory fields required in Leave Application")

    leave = frappe.get_doc({
        "doctype": "Leave Application",
        "employee": employee,
        "from_date": from_date,
        "to_date":to_date,
        "leave_type": leave_type,
        "description": description,
        "half_day": half_day,
        "half_day_date": half_day_date,
        "leave_approver_name": leave_approver
    })

    leave.insert()
    frappe.db.commit()

    name = get_first_doc_name("Leave Application", orderBy="modified DESC")

    return name

@frappe.whitelist()
def update_leave(name, from_date, to_date, leave_type, description, half_day = False, half_day_date = None):
    day = date_diff(to_date, from_date)
    if (day > 0 and half_day == True):
        if (half_day_date == None):
            raise Exception("Mandatory fields required in Leave Application")

    nowTime = now()
    if (half_day == True):
        frappe.db.sql(f"""
            UPDATE `tabLeave Application` 
            SET from_date='{from_date}',
            to_date='{to_date}',
            leave_type='{leave_type}',
            description="{description}",
            half_day={half_day},
            half_day_date="{half_day_date}",
            modified="{nowTime}"
            WHERE name='{name}';
        """)
    else :
        frappe.db.sql(f"""
            UPDATE `tabLeave Application` 
            SET from_date='{from_date}',
            to_date='{to_date}',
            leave_type='{leave_type}',
            description="{description}",
            half_day={half_day},
            modified="{nowTime}"
            WHERE name='{name}';
        """)
    frappe.db.commit()

    name = get_first_doc_name("Leave Application", orderBy="modified DESC")
    
    return name

@frappe.whitelist()
def delete_leave(name):
    frappe.delete_doc('Leave Application', name)
    return "Leave Application deleted"


@frappe.whitelist()
def leave_up_sbm(name, action):
    doc = frappe.db.get_list("Leave Application", filters={"name": name}, fields=["*"])
    
    doc[0].update({"doctype": "Leave Application"})
    val = apply_actions(frappe.parse_json(doc[0]), action)
    frappe.db.sql(f"""
        UPDATE `tabLeave Application` 
        SET workflow_state='{val.workflow_state}'
        WHERE name='{name}';
    """)
    frappe.db.commit()
    return val

@frappe.whitelist()
def get_doctype(doctype):
    getdoctype(doctype)

def get_first_doc_name(doctype, orderBy):
    doc = frappe.db.get_list(doctype, order_by=orderBy)

    return doc[0]
