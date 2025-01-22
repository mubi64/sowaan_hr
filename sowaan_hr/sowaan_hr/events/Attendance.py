import frappe

def late_approval(self, method):
    # frappe.msgprint("Late Approval")
    approval = frappe.get_all("Late Approval Request", filters={
    "employee":["=",self.employee],
    "docstatus": ["=", 1],
    "late_date": ["=", self.attendance_date]
    })

    if(len(approval) > 0):
        self.late_approved = True