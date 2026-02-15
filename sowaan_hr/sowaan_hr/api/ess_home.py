import frappe

def force_ess_redirect(bootinfo):
    if frappe.session.user == "Guest":
        return

    # Force override workspace routing
    bootinfo.home_page = "/app/ess"
    bootinfo.default_workspace = None
