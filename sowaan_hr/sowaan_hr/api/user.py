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

@frappe.whitelist()
def add_face_id(name, bytesImage):
    frappe.db.sql(f"""
        UPDATE `tabEmployee` 
        SET
        employee_face_id='{bytesImage}'
        WHERE name='{name}';
    """)
    frappe.db.commit()
    data = {}
    data["employee"] = frappe.get_doc('Employee', name)

    return data