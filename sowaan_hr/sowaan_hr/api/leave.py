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
    try:
        day = date_diff(to_date, from_date)
        if (day > 0 and half_day == True):
            if (half_day_date == None):
                raise Exception("Mandatory fields required in Leave Application")
        print(type(half_day),'hlf')
        leave = frappe.get_doc({
            "doctype": "Leave Application",
            "employee": employee,
            "from_date": from_date,
            "to_date":to_date,
            "leave_type": leave_type,
            "description": description,
            "half_day": True if half_day == "true" else False,
            "half_day_date": half_day_date,
            "leave_approver": leave_approver,
            "leave_approver_name": leave_approver
        })

        leave.insert()
        frappe.db.commit()

        name = get_first_doc_name("Leave Application", orderBy="modified DESC")

        return name
    
    except Exception as e:
        print('ExceptionErr',e)
        print(frappe.local.response,'check2')
        frappe.local.response['http_status_code'] = 500
        frappe.local.response['error_message'] = str(e)


@frappe.whitelist()
def update_leave(name, from_date, to_date, leave_type, description, half_day = False, half_day_date = None):
    try:
        doc = frappe.get_doc('Leave Application',name)   
        print(name, from_date, to_date, leave_type, description, half_day, half_day_date,'update Values')
        day = date_diff(to_date, from_date)
        if (day > 0 and half_day == True):
            if (half_day_date == None):
                raise Exception("Mandatory fields required in Leave Application")

        
        if (half_day == True):
            #  frappe.db.set_value('Leave Application',name, {
            # "from_date": from_date,
            # "to_date":to_date,
            # "leave_type": leave_type,
            # "description": description,
            # "half_day": half_day,
            # "half_day_date": half_day_date,
            # "modified":nowTime
            # })
       
            doc.from_date=from_date
            doc.to_date=to_date
            doc.leave_type=leave_type
            doc.description=description
            doc.half_day=half_day
            doc.half_day_date=half_day_date
            doc.save()
             
        else :
            # frappe.db.set_value('Leave Application',name, {
            # "from_date": from_date,
            # "to_date":to_date,
            # "leave_type": leave_type,
            # "description": description,
            # "half_day": half_day,
            # "modified":nowTime
            # })
            doc.from_date=from_date
            doc.to_date=to_date
            doc.leave_type=leave_type
            doc.description=description
            doc.half_day=half_day
            doc.save()

        #     frappe.db.sql(f"""
        #         UPDATE `tabLeave Application` 
        #         SET from_date='{from_date}',
        #         to_date='{to_date}',
        #         leave_type='{leave_type}',
        #         description="{description}",
        #         half_day={half_day},
        #         modified="{nowTime}"
        #         WHERE name='{name}';
        #     """)
        # frappe.db.commit()

        name = get_first_doc_name("Leave Application", orderBy="modified DESC")
        print(frappe.local.response,'check')
        return name
    except Exception as e:
        print('ExceptionErr',e)
        print(frappe.local.response,'check2')
        frappe.local.response['http_status_code'] = 500
        frappe.local.response['error_message'] = str(e)
    




@frappe.whitelist()
def delete_leave(name):
    frappe.delete_doc('Leave Application', name)
    return "Leave Application deleted"


@frappe.whitelist()
def leave_up_sbm(name, action):
    try:
        doc = frappe.db.get_list("Leave Application", filters={
                                "name": name}, fields=["*"])

        print('myaction',action)
        check_state = frappe.db.get_list('Workflow State',filters={'name': action}, fields=['*'])
        print(check_state,'myval')
        if(len(check_state) != 0):
            frappe.db.sql(f"""
                        UPDATE `tabLeave Application` 
                        SET status='{action}'
                        WHERE name='{name}';
                    """)
            frappe.db.commit()
        
            data = frappe.get_doc("Leave Application",name)
            val = apply_actions(frappe.parse_json(data),action)
            frappe.db.sql(f"""
                UPDATE `tabLeave Application` 
                SET workflow_state='{val.workflow_state}'
                WHERE name='{name}';
            """)
            frappe.db.commit()
            
            return val
        else:
            frappe.db.sql(f"""
                        UPDATE `tabLeave Application` 
                        SET status='Open'
                        WHERE name='{name}';
                    """)
            frappe.db.commit()
        
            data = frappe.get_doc("Leave Application",name)
            val = apply_actions(frappe.parse_json(data),action)
            frappe.db.sql(f"""
                UPDATE `tabLeave Application` 
                SET workflow_state='{val.workflow_state}'
                WHERE name='{name}';
            """)
            frappe.db.commit()
            
            return val
    except Exception as e:
        print('ExceptionErr',e)
        print(frappe.local.response,'check2')
        frappe.local.response['http_status_code'] = 500
        frappe.local.response['error_message'] = str(e)      
   

@frappe.whitelist()
def get_doctype(doctype):
    getdoctype(doctype)

def get_first_doc_name(doctype, orderBy):
    doc = frappe.db.get_list(doctype, order_by=orderBy)
    if doc:
        return doc[0]
    else:
        return None
