import frappe
from frappe import utils
from sowaan_hr.sowaan_hr.api.employee import get_allowed_employees, get_current_emp
from hrms.hr.doctype.leave_application.leave_application import get_leave_details

@frappe.whitelist()
def get_leave_list(employee):
    print(frappe.utils.nowdate())
    doc =  get_leave_details(employee, frappe.utils.nowdate())
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
        "Leave Type",
        filters=[['name', 'in',array_of_strings]]
    )
    
    return leaveTypeList

@frappe.whitelist()
def get_leave_allocation(employee):
    try:
        # leaveAllocation = frappe.db.get_list(
        #     "Leave Allocation",
        #     filters={"employee": employee, "docstatus": 1},
        #     fields=["leave_type", "total_leaves_allocated"]
        # )
        # doc =  get_leave_details(employee, frappe.utils.nowdate())

        # for obj in leaveAllocation:
        #     print(str(doc["leave_allocation"][obj.leave_type] == "Annual Leave"))
        #     if doc["leave_allocation"][obj.leave_type] == "Annual Leave":
        #         leave_types = obj.leave_type
        #         print(leave_types, "Check leave_types")
        #         val = doc["leave_allocation"][leave_types]
        #         print(val, "Check val")

        #         res = dict(
        #             leave_type = obj["leave_type"],
        #             total_leaves_allocation = obj["total_leaves_allocated"],
        #             leaves_taken = val["leaves_taken"],
        #             remaining_leaves = val["remaining_leaves"]
        #         )
        #         response.append(res)
        #     else:
        #         print("Helo")
        leave_details = get_leave_details(employee, frappe.utils.nowdate())
        leave_allocation = leave_details["leave_allocation"]
        response = [
                {
                    "leave_type": leave_type,
                    **leave_data
                } for leave_type, leave_data in leave_allocation.items()
            ]
        # response = dict(
        #     doc["leave_allocation"]
        # )

        return response
    except Exception as e:
        frappe.local.response['http_status_code'] = 500
        frappe.local.response['error_message'] = str(e)

@frappe.whitelist()
def get_leave_allocation_details(employee, leaveType):
    leaveAllocationDetails = frappe.db.get_list(
        "Leave Allocation",
        filters={"leave_type": leaveType},
        fields=["to_date"]
    )
    doc = get_leave_details(employee, frappe.utils.nowdate())
    response = doc["leave_allocation"][leaveType]
    response.update(leaveAllocationDetails[0])

    return response
