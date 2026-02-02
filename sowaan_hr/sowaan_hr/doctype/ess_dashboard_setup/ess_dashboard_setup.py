# Copyright (c) 2026, Sowaan and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe

@frappe.whitelist()
def get_expiry_fields(doctype):
    """Return only Date / Datetime fields (fieldname + label) for a DocType."""

    if not doctype:
        return []

    try:
        meta = frappe.get_meta(doctype)

        fields = [
            {
                "fieldname": df.fieldname,
                "label": df.label or df.fieldname.replace("_", " ").title()
            }
            for df in meta.fields
            if df.fieldtype in ("Date", "Datetime")
        ]

        return fields

    except Exception as e:
        frappe.log_error(
            message=str(e),
            title="ESS Dashboard: get_expiry_fields error"
        )
        return []

# @frappe.whitelist()
# def get_expiry_fields(doctype):
#     """Return all usable fields (fieldname + label) for a given DocType."""

#     if not doctype:
#         return []

#     try:
#         meta = frappe.get_meta(doctype)

#         fields = []

#         for df in meta.fields:
#             # Skip layout-only fields
#             if df.fieldtype in (
#                 "Section Break",
#                 "Column Break",
#                 "Tab Break",
#                 "HTML",
#                 "Button"
#             ):
#                 continue

#             fields.append({
#                 "fieldname": df.fieldname,
#                 "label": df.label or df.fieldname.replace("_", " ").title()
#             })

#         frappe.msgprint(f"Fields {fields}")
#         return fields

#     except Exception as e:
#         frappe.log_error(
#             message=str(e),
#             title="ESS Dashboard: get_expiry_fields error"
#         )
#         return []








class ESSDashboardSetup(Document):
	pass


@frappe.whitelist()
def get_child_tables(doctype, txt, searchfield, start, page_len, filters):
    parent_doctype = filters.get("doctype")

    if not parent_doctype:
        return []

    meta = frappe.get_meta(parent_doctype)

    child_tables = [
        df.options
        for df in meta.fields
        if df.fieldtype == "Table" and df.options
    ]

    # Return in Link field format
    return [
        [ct] for ct in child_tables if txt.lower() in ct.lower()
    ]


