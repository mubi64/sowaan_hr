import frappe

@frappe.whitelist()
def update_user_image(name, image):
    frappe.db.sql(f"""
        UPDATE `tabEmployee` 
        SET
        image='{image}'
        WHERE name='{name}';
    """)
    frappe.db.commit()

    return frappe.get_doc('Employee', name)