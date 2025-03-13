app_name = "sowaan_hr"
app_title = "Sowaan Hr"
app_publisher = "Sowaan"
app_description = "Modern HR features"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "info@sowaan.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "sowaan_hr",
# 		"logo": "/assets/sowaan_hr/logo.png",
# 		"title": "Sowaan Hr",
# 		"route": "/sowaan_hr",
# 		"has_permission": "sowaan_hr.api.permission.has_app_permission"
# 	}
# ]

fixtures = [
	{
		"doctype":"Custom Field",
		"filters":[
			[
				"fieldname",
                "in",
				(
					"gps_location", "marked_gps", "map", "checkout_entry", "required_hours", "allow_to_complete_required_hours_during_the_whole_month",
                    "late_approved", "custom_shift_roaster", "custom_fraction_of_total_earnings" , "custom_adjust_negative_salary" ,
					"custom_check_adjustment", "custom_is_half_day_fix", "custom_half_day_start_time", "custom_half_day_end_time",
                    "custom_total_half_days", "custom_early_exit_minutes", "custom_late_entry_minutes", "custom_allow_overtime" , "custom_required_hours",
                    "custom_ot_hours", "custom_overtime", "custom_overtime_hours_on_working_day", "custom_overtime_hours_on_holiday", "custom_column_break_hyfhy",
					"custom_overtime_per_hour_rate_for_working_day", "custom_overtime_per_hour_rate_for_holiday", "custom_smart_posting_date", "custom_payable", "custom_pay"
				)
			]
		]
	}
    # , 
	# {
	# 	"doctype":"Client Script",
	# 	"filters":[
	# 		[
	# 			"dt",
    #             "in",
	# 			(
	# 				"Employee Checkin"
	# 			)
	# 		]
	# 	]
	# },
	# {
	# 	"doctype":"Server Script",
	# 	"filters":[
	# 		[
	# 			"reference_doctype",
    #             "in",
	# 			(
	# 				"Attendance"
	# 			)
	# 		]
	# 	]
	# }
]


# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/sowaan_hr/css/sowaan_hr.css"
# app_include_js = "/assets/sowaan_hr/js/sowaan_hr.js"

# include js, css files in header of web template
# web_include_css = "/assets/sowaan_hr/css/sowaan_hr.css"
# web_include_js = "/assets/sowaan_hr/js/sowaan_hr.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "sowaan_hr/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Salary Slip" : "overrides/salary_slip.js" , 
    "Employee Checkin":"sowaan_hr/client_scripts/employee_checkin_form.js",
    "Payroll Entry" : "public/js/payroll_entry.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "sowaan_hr/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "sowaan_hr.utils.jinja_methods",
# 	"filters": "sowaan_hr.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "sowaan_hr.install.before_install"
# after_install = "sowaan_hr.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "sowaan_hr.uninstall.before_uninstall"
# after_uninstall = "sowaan_hr.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "sowaan_hr.utils.before_app_install"
# after_app_install = "sowaan_hr.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "sowaan_hr.utils.before_app_uninstall"
# after_app_uninstall = "sowaan_hr.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "sowaan_hr.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Payment Entry": "sowaan_hr.overrides.employee_payment_entry.EmployeePaymentEntry",
    "Salary Slip": "sowaan_hr.overrides.employee_salary_slip.EmployeeSalarySlip",
 	"Payroll Entry": "sowaan_hr.overrides.override_payroll_entry.OverridePayrollEntry",
    "Additional Salary": "sowaan_hr.overrides.employee_additional_salary.EmployeeAdditionalSalary"
}

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

doc_events = {
	"Salary Slip":{
		# "before_save": "sowaan_hr.sowaan_hr.doctype.arrears_process.arrears_process.add_arrears_to_earnings",
		"before_save": "sowaan_hr.sowaan_hr.events.Salary_slip.fund_management_and_negative_salary",
        # "before_save": "sowaan_hr.sowaan_hr.events.Salary_slip.before_save_salaryslip",
        "after_save" : "sowaan_hr.sowaan_hr.events.Salary_slip.own_fund_tax",

        # "before_save": "sowaan_hr.sowaan_hr.events.Salary_slip.set_fix_days",
        "before_submit": "sowaan_hr.sowaan_hr.events.Salary_slip.salary_slip_after_submit",
        "before_cancel": "sowaan_hr.sowaan_hr.events.Salary_slip.cancel_related_docs",
        "on_cancel": "sowaan_hr.sowaan_hr.events.Salary_slip.on_cancel",
	},
    "Loan Application":{
		"before_save": "sowaan_hr.sowaan_hr.events.loan_application.loan_withdrawal"
	},
    "Attendance":{
		"before_insert": "sowaan_hr.sowaan_hr.events.Attendance.late_approval",
        "validate": "sowaan_hr.sowaan_hr.events.Attendance.handle_half_day",
        "after_insert": "sowaan_hr.sowaan_hr.events.Attendance.after_insert_attendance"
        
	},
    "Shift Type":{
		"validate": "sowaan_hr.sowaan_hr.events.shift_type.half_day_msg"
	},
    "Journal Entry": {
        "before_submit": "sowaan_hr.sowaan_hr.events.journal_entry.after_submit",
        "on_cancel": "sowaan_hr.sowaan_hr.events.journal_entry.on_cancel",
	}
}


# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"sowaan_hr.tasks.all"
# 	],
# 	"daily": [
# 		"sowaan_hr.tasks.daily"
# 	],
# 	"hourly": [
# 		"sowaan_hr.tasks.hourly"
# 	],
# 	"weekly": [
# 		"sowaan_hr.tasks.weekly"
# 	],
# 	"monthly": [
# 		"sowaan_hr.tasks.monthly"
# 	],
# }

# Testing
# -------
advance_payment_doctypes = ["KSA Gratuity"]
# before_tests = "sowaan_hr.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "sowaan_hr.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "sowaan_hr.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["sowaan_hr.utils.before_request"]
# after_request = ["sowaan_hr.utils.after_request"]

# Job Events
# ----------
# before_job = ["sowaan_hr.utils.before_job"]
# after_job = ["sowaan_hr.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"sowaan_hr.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

