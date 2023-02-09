import frappe
from frappe.desk.form.load import getdoc
from sowaan_hr.sowaan_hr.api.employee import get_allowed_employees, get_current_emp
from sowaan_hr.sowaan_hr.api.workflow import apply_actions

@frappe.whitelist()
def get_checkin_request(employee, page):
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

    getCheckinList = frappe.db.get_list(
        "Employee Checkin Request",
        filters=filters,
        fields=['name', 
        'employee', 
        'employee_name', 
        'docstatus', 
        'workflow_state',
        'log_type', 
        'time', 
        'reason', 
        'checkin_marked'
        ],
        order_by="time desc",
        start=(page-1)*pageSize,
        page_length=pageSize,
    )

    return getCheckinList

@frappe.whitelist()
def get_permission(name):
    doctype = "Employee Checkin Request"
    getdoc(doctype, name)

@frappe.whitelist()
def create_checkin_request(employee, log_type, time, reason):
    request = frappe.get_doc({
        "doctype": "Employee Checkin Request",
        "employee": employee,
        "log_type": log_type,
        "time": time,
        "reason": reason
    })
    request.insert()
    frappe.db.commit()
    return "Checkin request created"

@frappe.whitelist()
def update_checkin_request(name, log_type, time, reason):
    frappe.db.sql(f"""
        UPDATE `tabEmployee Checkin Request` 
        SET log_type='{log_type}',
        time='{time}',
        reason="{reason}"
        WHERE name='{name}';
    """)
    frappe.db.commit()

    return "Checkin request updated"


@frappe.whitelist()
def checkin_request_up_sbm(name, action):
    doc = frappe.db.get_list("Employee Checkin Request", filters={"name": name}, fields=["*"])
    
    doc[0].update({"doctype": "Employee Checkin Request"})
    val = apply_actions(frappe.parse_json(doc[0]), action)
    frappe.db.sql(f"""
        UPDATE `tabEmployee Checkin Request` 
        SET workflow_state='{val.workflow_state}'
        WHERE name='{name}';
    """)
    frappe.db.commit()
    return val