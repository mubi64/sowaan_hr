import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, get_last_day


class ProjectWorkDistribution(Document):

    # -------------------------------------------------
    # VALIDATE (runs on every save)
    # -------------------------------------------------
    def validate(self):
        self.validate_overtime_rules()
        self.calculate_cost_center_percentages()

    # -------------------------------------------------
    # SUBMIT (runs once)
    # -------------------------------------------------
    def on_submit(self):
        if not self.project_details:
            frappe.throw(_("Cannot submit without Project Details"))

        self.create_salary_structure_assignment()

    # -------------------------------------------------
    # OVERTIME RULES (SERVER-SIDE AUTHORITY)
    # -------------------------------------------------
    def validate_overtime_rules(self):
        for d in self.project_details:

            # Working Day OT NOT allowed on holidays
            if d.holiday:
                d.working_days_overtime = 0

            # Holiday OT only if Present on holiday
            if not (d.holiday and d.attendance_status == "Present"):
                d.holiday_overtime = 0

            # Prevent negative values
            if (d.working_days_overtime or 0) < 0:
                d.working_days_overtime = 0

            if (d.holiday_overtime or 0) < 0:
                d.holiday_overtime = 0

    # -------------------------------------------------
    # COST CENTER PERCENTAGE CALCULATION
    # -------------------------------------------------
    def calculate_cost_center_percentages(self):

        if not self.project_details:
            frappe.throw(_("Please load attendance first."))

        cc_units = {}
        total_units = 0.0

        for d in self.project_details:
            units = 1.0

            # Working day OT
            if not d.holiday:
                units += (d.working_days_overtime or 0) / 8.0

            # Holiday OT
            if d.holiday:
                units += (d.holiday_overtime or 0) / 8.0

            cc = d.cost_center or "UNKNOWN"
            cc_units[cc] = cc_units.get(cc, 0) + units
            total_units += units

        if total_units <= 0:
            frappe.throw(_("Total work units cannot be zero."))

        cc_percentages = {}
        running_total = 0
        cc_list = list(cc_units.keys())

        for cc in cc_list:
            pct = int((cc_units[cc] / total_units) * 100)
            cc_percentages[cc] = pct
            running_total += pct

        # Fix rounding difference
        remainder = 100 - running_total
        if remainder and cc_list:
            cc_percentages[cc_list[-1]] += remainder

        for d in self.project_details:
            d.percentage = cc_percentages.get(d.cost_center or "UNKNOWN", 0)

    # -------------------------------------------------
    # SALARY STRUCTURE ASSIGNMENT CREATION
    # -------------------------------------------------
    def create_salary_structure_assignment(self):

        if not self.employee:
            frappe.throw(_("Employee is required."))

        if not self.project_details:
            frappe.throw(_("No Project Work Distribution details found."))

        if not self.salary_structure:
            frappe.throw(_("Please select a Salary Structure."))

        from_date = getdate(self.from_date)
        to_date = get_last_day(from_date)

        # Prevent duplicate assignment for same month
        if frappe.db.exists(
            "Salary Structure Assignment",
            {
                "employee": self.employee,
                "from_date": from_date,
                "docstatus": ["<", 2]
            }
        ):
            frappe.msgprint(
                _("Salary Structure Assignment already exists for this employee and month.")
            )
            return

        # ---------------- CREATE SSA ----------------
        new_ssa = frappe.new_doc("Salary Structure Assignment")
        new_ssa.employee = self.employee
        new_ssa.salary_structure = self.salary_structure   # ✅ FROM FORM
        new_ssa.company = self.company
        new_ssa.from_date = from_date
        new_ssa.to_date = to_date
        new_ssa.payroll_frequency = "Monthly"
        new_ssa.custom_project_work_distribution = self.name
        new_ssa.base = self.base

        # ---------------- COST CENTER DISTRIBUTION ----------------
        added_cc = set()

        for d in self.project_details:
            if not d.cost_center or d.cost_center in added_cc:
                continue

            added_cc.add(d.cost_center)

            new_ssa.append("payroll_cost_centers", {
                "cost_center": d.cost_center,
                "percentage": d.percentage or 0
            })

        if not new_ssa.payroll_cost_centers:
            frappe.throw(
                _("No valid Cost Centers found to assign payroll distribution.")
            )

        new_ssa.insert(ignore_permissions=True)
        new_ssa.submit()

        frappe.msgprint(
            _("✅ Salary Structure Assignment created successfully: <b>{0}</b>")
            .format(new_ssa.name)
        )



# -------------------------------------------------
# WHITELISTED METHOD (AJAX CALL FROM JS)
# -------------------------------------------------
@frappe.whitelist()
def get_attendance_preview(employee, from_date, to_date, company):

    if not employee or not from_date or not to_date or not company:
        frappe.throw(_("Missing required parameters"))

    result = []

    attendance_rows = frappe.get_all(
        "Attendance",
        filters={
            "employee": employee,
            "attendance_date": ["between", [from_date, to_date]]
        },
        fields=["attendance_date", "status"],
        order_by="attendance_date asc"
    )

    for att in attendance_rows:
        date_str = str(att.attendance_date)

        is_holiday = 1 if frappe.get_all(
            "Holiday",
            filters={"holiday_date": date_str},
            limit_page_length=1
        ) else 0

        start_ts = f"{date_str} 00:00:00"
        end_ts = f"{date_str} 23:59:59"

        checkins = frappe.get_all(
            "Employee Checkin",
            filters=[
                ["employee", "=", employee],
                ["time", "between", [start_ts, end_ts]]
            ],
            fields=["device_id"],
            order_by="time asc",
            limit_page_length=1
        )

        cost_center = ""
        if checkins:
            device_id = checkins[0].get("device_id")
            if device_id:
                cc = frappe.get_all(
                    "Cost Center",
                    filters={
                        "device_id": device_id,
                        "company": company
                    },
                    fields=["name"],
                    limit_page_length=1
                )
                if cc:
                    cost_center = cc[0].name

        result.append({
            "date": att.attendance_date,
            "attendance_status": att.status,
            "holiday": is_holiday,
            "cost_center": cost_center
        })

    return result
