// ======================================================
// GLOBAL STATE
// ======================================================
let allow_overtime = false;

// ======================================================
// PARENT DOCTYPE
// ======================================================
frappe.ui.form.on("Project Work Distribution", {

    refresh(frm) {

        // -------------------------------
        // GET ATTENDANCE BUTTON
        // -------------------------------
        frm.add_custom_button("Get Employee Attendance", () => {

            if (!frm.doc.employee || !frm.doc.from_date || !frm.doc.to_date) {
                frappe.msgprint(
                    __("Please select Employee, From Date and To Date first.")
                );
                return;
            }

            frappe.call({
                method: "sowaan_hr.sowaan_hr.doctype.project_work_distribution.project_work_distribution.get_attendance_preview",
                args: {
                    employee: frm.doc.employee,
                    from_date: frm.doc.from_date,
                    to_date: frm.doc.to_date,
                    company: frm.doc.company
                },
                freeze: true,
                freeze_message: __("Fetching attendance...")
            }).then(r => {

                const rows = r.message || [];
                frm.clear_table("project_details");

                rows.forEach(d => {
                    let row = frm.add_child("project_details");
                    row.date = d.date;
                    row.attendance_status = d.attendance_status;
                    row.holiday = d.holiday;
                    row.cost_center = d.cost_center;
                    row.days_worked = 1;
                    row.working_days_overtime = 0;
                    row.holiday_overtime = 0;
                });

                frm.refresh_field("project_details");

                // Prompt missing attendance
                prompt_missing_attendance(frm, rows);

                apply_overtime_rules(frm);
            });
        });

        apply_overtime_rules(frm);
    },

    employee(frm) {
        allow_overtime = false;

        if (!frm.doc.employee) {
            apply_overtime_rules(frm);
            return;
        }

        frappe.db.get_value(
            "Employee",
            frm.doc.employee,
            "custom_calculate_overtime_as_per_timesheet"
        ).then(r => {
            allow_overtime = !!r.message?.custom_calculate_overtime_as_per_timesheet;
            apply_overtime_rules(frm);
        });
    }
});

// ======================================================
// CHILD TABLE EVENTS
// ======================================================
frappe.ui.form.on("Projects Worked On", {

    days_worked(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        if ((row.days_worked || 0) < 0) {
            row.days_worked = 0;
            frappe.msgprint(__("Working Days cannot be negative."));
            frm.refresh_field("project_details");
        }
    },

    holiday(frm, cdt, cdn) {
        enforce_row_rules(frm, cdt, cdn);
    },

    attendance_status(frm, cdt, cdn) {
        enforce_row_rules(frm, cdt, cdn);
    },

    working_days_overtime(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (!allow_overtime) {
            row.working_days_overtime = 0;
            frappe.msgprint(__("Overtime is not allowed for this employee."));
        }

        if (cint(row.holiday) === 1) {
            row.working_days_overtime = 0;
            frappe.msgprint(__("Working Day Overtime is not allowed on holidays."));
        }

        if ((row.working_days_overtime || 0) < 0) {
            row.working_days_overtime = 0;
        }

        frm.refresh_field("project_details");
    },

    holiday_overtime(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (!allow_overtime) {
            row.holiday_overtime = 0;
            frappe.msgprint(__("Overtime is not allowed for this employee."));
        }

        if (cint(row.holiday) !== 1) {
            row.holiday_overtime = 0;
            frappe.msgprint(__("Holiday Overtime is allowed only on holidays."));
        }

        if (row.attendance_status !== "Present") {
            row.holiday_overtime = 0;
            frappe.msgprint(
                __("Holiday Overtime is allowed only when employee is Present.")
            );
        }

        if ((row.holiday_overtime || 0) < 0) {
            row.holiday_overtime = 0;
        }

        frm.refresh_field("project_details");
    }
});

// ======================================================
// GRID-LEVEL RULES (UI ONLY)
// ======================================================
function apply_overtime_rules(frm) {

    if (!frm.fields_dict.project_details) return;

    // Column-level enable ONLY for working day OT
    frm.fields_dict.project_details.grid.toggle_enable(
        "working_days_overtime",
        allow_overtime
    );

    // Column-level enable ONLY for holiday OT
    frm.fields_dict.project_details.grid.toggle_enable(
        "holiday_overtime",
        allow_overtime
    );
}

// ======================================================
// ROW-LEVEL RULE ENFORCEMENT
// ======================================================
function enforce_row_rules(frm, cdt, cdn) {

    let row = locals[cdt][cdn];

    // HOLIDAY ROW
    if (cint(row.holiday) === 1) {

        row.working_days_overtime = 0;

        if (row.attendance_status !== "Present") {
            row.holiday_overtime = 0;
        }

    }
    // WORKING DAY ROW
    else {
        row.holiday_overtime = 0;
    }

    frm.refresh_field("project_details");
}

// ======================================================
// MISSING ATTENDANCE PROMPT
// ======================================================
function prompt_missing_attendance(frm, attendance_rows) {

    if (!attendance_rows || !attendance_rows.length) return;

    const from_date = frappe.datetime.str_to_obj(frm.doc.from_date);
    const to_date = frappe.datetime.str_to_obj(frm.doc.to_date);

    const present_dates = attendance_rows.map(r => r.date);
    let missing_dates = [];

    let current = new Date(from_date);

    while (current <= to_date) {
        const date_str = frappe.datetime.obj_to_str(current);

        if (!present_dates.includes(date_str)) {
            missing_dates.push(date_str);
        }

        current.setDate(current.getDate() + 1);
    }

    if (missing_dates.length) {
        frappe.msgprint({
            title: __("⚠️ Missing Attendance"),
            indicator: "orange",
            message: __(
                "Attendance is missing for the following dates:<br><br><b>{0}</b>"
            ).format(missing_dates.join(", "))
        });
    }
}
