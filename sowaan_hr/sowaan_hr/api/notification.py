import frappe

@frappe.whitelist()
def get_notification_log(page):
    pageSize = 20
    page = int(page)
    
    if(page <= 0):
        return "Page should be greater or equal of 1"

    logs = frappe.db.get_list(
        "Notification Log",
        fields=["*"],
        order_by="creation desc",
        start=(page-1)*pageSize,
        page_length=pageSize,
    )

    return logs

@frappe.whitelist()
def get_notification_length():
    logs = frappe.db.get_list(
        "Notification Log")
    total_count = len(logs)
    return total_count