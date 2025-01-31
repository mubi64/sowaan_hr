// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Sowaan HR Settings", {
    refresh(frm) {
        set_required_fields(frm);
    },
    is_late_deduction_applicable(frm) {
        set_required_fields(frm);
    },
    is_early_deduction_applicable(frm) {
        set_required_fields(frm);
    },
    is_half_day_deduction_applicable(frm) {
        set_required_fields(frm);
    }
});

function set_required_fields(frm) {
    frm.set_df_property('late_salary_component', 'reqd', frm.doc.is_late_deduction_applicable ? 1 : 0);

    frm.set_df_property('early_salary_component', 'reqd', frm.doc.is_early_deduction_applicable ? 1 : 0);
    
    frm.set_df_property('half_day_salary_component', 'reqd', frm.doc.is_half_day_deduction_applicable ? 1 : 0);
}
