import frappe
from frappe.query_builder import DocType
from frappe.model.workflow import get_transitions, apply_workflow

@frappe.whitelist()
def get_checkin_actions(name):
    doc = {
        "name": name,
        "doctype": "Employee Checkin Request"
    }
    workflow = get_transitions(doc)
    
    return workflow

@frappe.whitelist()
def get_leave_actions(name):
    doc = {
        "name": name,
        "doctype": "Leave Application"
    }
    workflow = get_transitions(doc)
    return workflow

@frappe.whitelist()
def get_loan_actions(name):
    try:
        doc = {
            "name": name,
            "doctype": "Loan Application"
        }
        workflow = get_transitions(doc)
        
        return workflow
    except Exception as e:
        frappe.local.response['http_status_code'] = 500
        frappe.local.response['error_message'] = str(e._error_message)


@frappe.whitelist()
def get_late_approval_actions(name):
    doc = {
        "name": name,
        "doctype": "Late Approval Request"
    }
    workflow = get_transitions(doc)
    
    return workflow
    
@frappe.whitelist()
def apply_actions(doc, action):
    workflow = apply_workflow(doc, action)
    
    return workflow