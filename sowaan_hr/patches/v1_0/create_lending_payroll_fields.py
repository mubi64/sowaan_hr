import frappe


def execute():
	"""Create the HRMS <-> Lending payroll integration custom fields.

	hrms.setup.after_app_install() only fires when `lending` is installed *after* hrms.
	Where lending was installed first, hrms had no Loan doctype to attach to and the
	hook never ran again, leaving Loan.repay_from_salary (and the related Loan
	Repayment / Salary Slip fields and ESS docperms) missing.

	No-ops on sites that don't have both apps, or that already have the fields.
	"""
	installed = frappe.get_installed_apps()
	if "hrms" not in installed or "lending" not in installed:
		return

	if frappe.db.exists("Custom Field", {"dt": "Loan", "fieldname": "repay_from_salary"}):
		return

	from hrms.setup import after_app_install

	after_app_install("lending")
