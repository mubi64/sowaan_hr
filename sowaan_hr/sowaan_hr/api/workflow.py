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

@frappe.whitelist()
def get_doctype_workflow_status(doctype):
    workflow = frappe.get_doc("Workflow", doctype)
    if workflow.is_active == 1:
        allstatus = set(sta.state for sta in workflow.states)
        return [{"status": state} for state in list(allstatus)]
    else:
        return []