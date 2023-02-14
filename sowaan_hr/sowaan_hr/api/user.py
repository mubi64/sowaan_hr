import frappe

@frappe.whitelist()
def update_user_image(email, url):
    frappe.db.sql(f"""
        UPDATE `tabUser` 
        SET
        user_image='{url}'
        WHERE email='{email}';
    """)
    frappe.db.commit()

    return frappe.db.get_list("User", fields=["*"])