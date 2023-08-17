import frappe
from frappe import utils
from sowaan_hr.sowaan_hr.api.employee import get_allowed_employees, get_current_emp
from erpnext.hr.doctype.leave_application.leave_application import get_leave_details


@frappe.whitelist()
def get_leave_list(employee):
    print(frappe.utils.nowdate())
    doc = get_leave_details(employee, frappe.utils.nowdate())
    response = dict(
        doc["leave_allocation"]
    )
    print(f"\n\n\n {response} \n\n\n")
    return doc


@frappe.whitelist()
def get_leave_types(employee):
    leaveAllocation = frappe.db.get_list(
        "Leave Allocation",
        filters={"employee": employee, "docstatus": 1},
        fields=["leave_type", "total_leaves_allocated"]
    )
   
    array_of_strings = [obj["leave_type"] for obj in leaveAllocation]
    leaveTypeList = frappe.db.get_list(
        "Leave Type",filters=[[
    'name', 'in',array_of_strings
        ]]
    )
    print(array_of_strings)
    print(leaveTypeList,'value',employee)
    return leaveTypeList

@frappe.whitelist()
def get_leave_allocation(employee):
    response = []
    leaveAllocation = frappe.db.get_list(
        "Leave Allocation",
        filters={"employee": employee, "docstatus": 1},
        fields=["leave_type", "total_leaves_allocated"]
    )
    doc = get_leave_details(employee, frappe.utils.nowdate())

    for key in leaveAllocation:
        obj = key
        leave_types = key.leave_type
        val = doc["leave_allocation"][leave_types]
        res = dict(
            leave_type=obj["leave_type"],
            total_leaves_allocation=float(obj["total_leaves_allocated"]),
            leaves_taken=float(val["leaves_taken"]),
            remaining_leaves=float(val["remaining_leaves"]),
            leaves_pending_approval=float(val["leaves_pending_approval"]),
        )
        response.append(res)

    return response


@frappe.whitelist()
def get_leave_allocation_details(employee, leaveType):
    leaveAllocationDetails = frappe.db.get_list(
        "Leave Allocation",
        filters={"leave_type": leaveType},
        fields=["to_date"]
    )
    if(len(leaveAllocationDetails) > 0):
        doc = get_leave_details(employee, frappe.utils.nowdate())
        
        response = doc["leave_allocation"][leaveType]
        response.update(leaveAllocationDetails[0])
        response['leaves_taken'] = float(response['leaves_taken'])
        response['expired_leaves'] = float(response['expired_leaves'])
        
        return response
    else:
        frappe.throw("You don't have the leaves of this type")