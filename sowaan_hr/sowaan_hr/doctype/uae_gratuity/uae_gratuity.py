# Copyright (c) 2024, Sowaan and contributors
# For license information, please see license.txt

from math import (floor, ceil)
import datetime
from dateutil import relativedelta

import frappe
from frappe import _, bold
from frappe.query_builder.functions import Sum
from frappe.utils import flt, get_datetime, get_link_to_form

from erpnext.accounts.general_ledger import make_gl_entries
from erpnext.controllers.accounts_controller import AccountsController


class UAEGratuity(AccountsController):
	def validate(self):
		data = calculate_work_experience_and_amount(self.employee, self.gratuity_rule)
		self.current_work_experience = data["current_work_experience"]
		self.years = data["years"]
		self.months = data["months"]
		self.days = data["days"]
		self.normal_amount = data["amount"]
		self.max_gratuity_amount = flt(data["max_amount"]) * flt(self.max_gratuity_months)
		self.amount = self.max_gratuity_amount if self.normal_amount > self.max_gratuity_amount else self.normal_amount
		self.set_status()

	def set_status(self, update=False):
		precision = self.precision("paid_amount")
		
		status = None

		if self.docstatus == 0:
			status = "Draft"
		elif self.docstatus == 1:
			if flt(self.paid_amount) > 0 and flt(self.amount, precision) == flt(
				self.paid_amount, precision
			):
				status = "Paid"
			else:
				status = "Unpaid"
		elif self.docstatus == 2:
			status = "Cancelled"

		if update:
			self.db_set("status", status)
		else:
			self.status = status


	def on_submit(self):
		if self.pay_via_salary_slip:
			self.create_additional_salary()
		else:
			self.create_gl_entries()

	def on_cancel(self):
		self.ignore_linked_doctypes = ["GL Entry"]
		self.set_status(update=True)
		if self.pay_via_salary_slip == 0:
			self.create_gl_entries(cancel=True)

	def create_gl_entries(self, cancel=False):
		gl_entries = self.get_gl_entries()
		make_gl_entries(gl_entries, cancel)

	def get_gl_entries(self):
		gl_entry = []
		# payable entry
		if self.amount:
			gl_entry.append(
				self.get_gl_dict(
					{
						"account": self.payable_account,
						"credit": self.amount,
						"credit_in_account_currency": self.amount,
						"against": self.expense_account,
						"party_type": "Employee",
						"party": self.employee,
						"against_voucher_type": self.doctype,
						"against_voucher": self.name,
						"cost_center": self.cost_center,
					},
					item=self,
				)
			)

			# expense entries
			gl_entry.append(
				self.get_gl_dict(
					{
						"account": self.expense_account,
						"debit": self.amount,
						"debit_in_account_currency": self.amount,
						"against": self.payable_account,
						"cost_center": self.cost_center,
					},
					item=self,
				)
			)
		else:
			frappe.throw(_("Total Amount can not be zero"))

		return gl_entry

	def create_additional_salary(self):
		if self.pay_via_salary_slip:
			additional_salary = frappe.new_doc("Additional Salary")
			additional_salary.employee = self.employee
			additional_salary.salary_component = self.salary_component
			additional_salary.overwrite_salary_structure_amount = 0
			additional_salary.amount = self.amount
			additional_salary.payroll_date = self.payroll_date
			additional_salary.company = self.company
			additional_salary.ref_doctype = self.doctype
			additional_salary.ref_docname = self.name
			additional_salary.submit()

	def set_total_advance_paid(self):
		gle = frappe.qb.DocType("GL Entry")
		paid_amount = (
			frappe.qb.from_(gle)
			.select(Sum(gle.debit_in_account_currency).as_("paid_amount"))
			.where(
				(gle.against_voucher_type == "UAE Gratuity")
				& (gle.against_voucher == self.name)
				& (gle.party_type == "Employee")
				& (gle.party == self.employee)
				& (gle.docstatus == 1)
				& (gle.is_cancelled == 0)
			)
		).run(as_dict=True)[0].paid_amount or 0

		if flt(paid_amount) > self.amount:
			frappe.throw(_("Row {0}# Paid Amount cannot be greater than Total amount"))
		print(paid_amount, "I want to check Paid amount set or not \n\n\n\n")
		self.db_set("paid_amount", paid_amount)
		self.set_status(update=True)


@frappe.whitelist()
def calculate_work_experience_and_amount(employee, gratuity_rule):
	data = calculate_work_experience(employee, gratuity_rule)
	values = calculate_gratuity_amount(employee, gratuity_rule, data)

	return {
		"current_work_experience": data["current_work_experience"], 
		"years": data["years"],
		"months": data["months"],
		"days": data["days"],
		"amount": values["gratuity_amount"] or 0,
		"max_amount": values["total_applicable_components_amount"] or 0}


def calculate_work_experience(employee, gratuity_rule):

	total_working_days_per_year, minimum_year_for_gratuity = frappe.db.get_value(
		"Gratuity Rule", gratuity_rule, ["total_working_days_per_year", "minimum_year_for_gratuity"]
	)

	date_of_joining, relieving_date = frappe.db.get_value(
		"Employee", employee, ["date_of_joining", "relieving_date"]
	)
	if not relieving_date:
		frappe.throw(
			_("Please set Relieving Date for employee: {0}").format(
				bold(get_link_to_form("Employee", employee))
			)
		)

	method = frappe.db.get_value(
		"Gratuity Rule", gratuity_rule, "work_experience_calculation_function"
	)
	data = calculate_employee_total_workings_days(
		employee, date_of_joining, relieving_date
	)

	employee_total_workings_days = data["employee_total_workings_days"]
	non_working_days = data["non_working_days"]
	
	# print(employee_total_workings_days, non_working_days)
	# days_per_year = 365.2 if consider_exact_days_per_year == 1 else total_working_days_per_year

	current_work_experience = employee_total_workings_days / total_working_days_per_year or 1
	current_work_experience = get_work_experience_using_method(
		method, current_work_experience, minimum_year_for_gratuity, employee
	)
	# days_in_month = days_per_year/12
	# years = floor(employee_total_workings_days/days_per_year)
	# months = floor((employee_total_workings_days - (years*days_per_year))/days_in_month)
	# days = employee_total_workings_days - (months*days_in_month) - (years*days_per_year)
	
	relieving_date = get_datetime(relieving_date)+datetime.timedelta(days=1)
	relieving_date = get_datetime(relieving_date)+datetime.timedelta(days=-non_working_days)

	date_diff = relativedelta.relativedelta(relieving_date, date_of_joining)


	# print('employee_total_workings_days****')
	# print(relieving_date)
	# print(employee_total_workings_days)
	# print(days_in_month)
	# print(days_per_year)
	return {
		"current_work_experience":current_work_experience,
		"years": date_diff.years,
		"months": date_diff.months,
		"days": date_diff.days
		}


def calculate_employee_total_workings_days(employee, date_of_joining, relieving_date):
	# employee_total_workings_days = ((get_datetime(relieving_date)+datetime.timedelta(days=1)) - get_datetime(date_of_joining)).days
	employee_total_workings_days = ((get_datetime(relieving_date)) - get_datetime(date_of_joining)).days
	non_working_days = 0
	payroll_based_on = frappe.db.get_value("Payroll Settings", None, "payroll_based_on") or "Leave"
	if payroll_based_on == "Leave":
		total_lwp = get_non_working_days(employee, relieving_date, "On Leave")
		employee_total_workings_days -= total_lwp
		non_working_days = total_lwp
	elif payroll_based_on == "Attendance":
		total_absents = get_non_working_days(employee, relieving_date, "Absent")
		employee_total_workings_days -= total_absents
		non_working_days = total_absents

	return { 
		"employee_total_workings_days":employee_total_workings_days, 
		"non_working_days":non_working_days
		}


def get_work_experience_using_method(
	method, current_work_experience, minimum_year_for_gratuity, employee
):
	if method == "Round off Work Experience":
		current_work_experience = round(current_work_experience)
	else:
		current_work_experience = (current_work_experience)

	if current_work_experience < minimum_year_for_gratuity:
		frappe.throw(
			_("Employee: {0} have to complete minimum {1} years for gratuity").format(
				bold(employee), minimum_year_for_gratuity
			)
		)
	return current_work_experience


def get_non_working_days(employee, relieving_date, status):

	filters = {
		"docstatus": 1,
		"status": status,
		"employee": employee,
		"attendance_date": ("<=", get_datetime(relieving_date)),
	}

	if status == "On Leave":
		lwp_leave_types = frappe.get_list("Leave Type", filters={"is_lwp": 1})
		lwp_leave_types = [leave_type.name for leave_type in lwp_leave_types]
		filters["leave_type"] = ("IN", lwp_leave_types)

	record = frappe.get_all("Attendance", filters=filters, fields=["COUNT(name) as total_lwp"])
	return record[0].total_lwp if len(record) else 0


def calculate_gratuity_amount(employee, gratuity_rule, experience):
	# applicable_amount = 0
	applicable_earnings_component = get_applicable_components(gratuity_rule)
	# print(applicable_earnings_component)
	total_applicable_components_amount = get_total_applicable_component_amount(
		employee, applicable_earnings_component, gratuity_rule
	)

	calculate_gratuity_amount_based_on = frappe.db.get_value(
		"Gratuity Rule", gratuity_rule, "calculate_gratuity_amount_based_on"
	)
	gratuity_amount = 0
	slabs = get_gratuity_rule_slabs(gratuity_rule)
	slab_found = False
	year_left = experience["years"]
	months = experience["months"]
	days = experience["days"]

	fraction_of_total = 1
	
	for slab in slabs:
		amount = total_applicable_components_amount * slab.fraction_of_applicable_earnings	
		if calculate_gratuity_amount_based_on == "Current Slab":
			# applicable_amount = total_applicable_components_amount * slab.fraction_of_applicable_earnings
			slab_found, gratuity_amount = calculate_amount_based_on_current_slab(
				slab.from_year,
				slab.to_year,
				experience["current_work_experience"],
				total_applicable_components_amount,
				slab.fraction_of_applicable_earnings,
			)
			if slab_found:
				break

		elif calculate_gratuity_amount_based_on == "Sum of all previous slabs":
			# print(gratuity_amount, amount, "amount \n\n\n\n\n")
			if slab.to_year == 0 and slab.from_year == 0:
				# applicable_amount += amount
				gratuity_amount += (
					year_left * amount
				)
				gratuity_amount += (
					(amount/12)*months
				)
				gratuity_amount += (
					(amount/12/30)*days
				)
				slab_found = True
				fraction_of_total = slab.custom_fraction_of_total_earnings
				break
			if experience["current_work_experience"] >= slab.to_year and experience["current_work_experience"] > slab.from_year and slab.to_year != 0:
				print(amount, "amount", slab.to_year, "-", slab.from_year, (slab.to_year - slab.from_year), "checking condition 318 \n\n\n\n\n")
				gratuity_amount += (
					(slab.to_year - slab.from_year)
					* amount
				)
				# print(gratuity_amount, "gratuity_amount 323 ********")
				# applicable_amount += (
				# 	(slab.to_year - slab.from_year)
				# 	* amount
				# )
				year_left -= (slab.to_year - slab.from_year)
				slab_found = True
				fraction_of_total = slab.custom_fraction_of_total_earnings
			elif slab.from_year <= experience["current_work_experience"] and (experience["current_work_experience"] < slab.to_year or slab.to_year == 0):
				# print('(year_left)')
				# print(experience["current_work_experience"])
				# print(year_left)
				# print(gratuity_amount, year_left, amount, months, days, "checkings	 values \n\n\n\n\n")
				gratuity_amount += (
					year_left * amount
				)
				gratuity_amount += (
					(amount/12)*months
				)
				gratuity_amount += (
					(amount/12/30)*days
				)
				# applicable_amount += amount
				slab_found = True

				if year_left > 0 or months > 0 or days > 0:
					fraction_of_total = slab.custom_fraction_of_total_earnings
				# print(fraction_of_total, slab, "'fraction_of_total")
	
	if not slab_found:
		frappe.throw(
			_("No Suitable Slab found for Calculation of gratuity amount in Gratuity Rule: {0}").format(
				bold(gratuity_rule)
			)
		)
	# print(gratuity_amount, fraction_of_total, applicable_amount, "fraction_of_total and gratuity \n\n\n\n")

	return {"total_applicable_components_amount": total_applicable_components_amount, "gratuity_amount": flt(gratuity_amount)*flt(fraction_of_total)}


def get_applicable_components(gratuity_rule):
	applicable_earnings_component = frappe.get_all(
		"Gratuity Applicable Component", filters={"parent": gratuity_rule}, fields=["salary_component"]
	)
	if len(applicable_earnings_component) == 0:
		frappe.throw(
			_("No Applicable Earnings Component found for Gratuity Rule: {0}").format(
				bold(get_link_to_form("Gratuity Rule", gratuity_rule))
			)
		)
	applicable_earnings_component = [
		component.salary_component for component in applicable_earnings_component
	]

	return applicable_earnings_component


def get_total_applicable_component_amount(employee, applicable_earnings_component, gratuity_rule):
	sal_slip = get_last_salary_slip(employee)
	if not sal_slip:
		frappe.throw(_("No Salary Slip is found for Employee: {0}").format(bold(employee)))
	component_and_amounts = frappe.get_all(
		"Salary Detail",
		filters={
			"docstatus": 1,
			"parent": sal_slip,
			"parentfield": "earnings",
			"salary_component": ("in", applicable_earnings_component),
		},
		fields=["amount"],
	)
	total_applicable_components_amount = 0
	if not len(component_and_amounts):
		frappe.throw(_("No Applicable Component is present in last month salary slip"))
	for data in component_and_amounts:
		total_applicable_components_amount += data.amount
	return total_applicable_components_amount


def calculate_amount_based_on_current_slab(
	from_year,
	to_year,
	experience,
	total_applicable_components_amount,
	fraction_of_applicable_earnings,
):
	slab_found = False
	gratuity_amount = 0
	print(total_applicable_components_amount, "*", experience, "*", fraction_of_applicable_earnings, "checking values")
	if experience >= from_year and (to_year == 0 or experience < to_year):
		gratuity_amount = (
			total_applicable_components_amount * experience * fraction_of_applicable_earnings
		)
		if fraction_of_applicable_earnings:
			slab_found = True

	return slab_found, gratuity_amount


def get_gratuity_rule_slabs(gratuity_rule):
	return frappe.get_all(
		"Gratuity Rule Slab", filters={"parent": gratuity_rule}, fields=["*"], order_by="idx"
	)


def get_salary_structure(employee):
	return frappe.get_list(
		"Salary Structure Assignment",
		filters={"employee": employee, "docstatus": 1},
		fields=["from_date", "salary_structure"],
		order_by="from_date desc",
	)[0].salary_structure


def get_last_salary_slip(employee):
	salary_slips = frappe.get_list(
		"Salary Slip", filters={"employee": employee, "docstatus": 1}, order_by="start_date desc"
	)
	if not salary_slips:
		return
	return salary_slips[0].name

