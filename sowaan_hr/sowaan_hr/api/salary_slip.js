
frappe.ui.form.on('Salary Slip', {
    custom_adjust_negative_salary(frm) {

        frm.set_value('custom_check_adjustment', frm.doc.custom_adjust_negative_salary ? 1 : 0);
        
    },
    onload(frm) {
        get_hr_settings(frm);
    },
    refresh(frm) {
        get_hr_settings(frm);
    },
    validate(frm) {
        get_hr_settings(frm);
    }
});



function get_hr_settings(frm) {
    frappe.db.get_single_value('Sowaan HR Settings', 'is_late_deduction_applicable')
    .then(is_late_deduction_applicable => {
        set_field_visibility(frm, 'custom_late_entry_minutes', is_late_deduction_applicable);
    });

    frappe.db.get_single_value('Sowaan HR Settings', 'is_early_deduction_applicable')
    .then(is_early_deduction_applicable => {
        set_field_visibility(frm, 'custom_early_exit_minutes', is_early_deduction_applicable);
    });

    frappe.db.get_single_value('Sowaan HR Settings', 'is_half_day_deduction_applicable')
    .then(is_half_day_deduction_applicable => {
        set_field_visibility(frm, 'custom_total_half_days', is_half_day_deduction_applicable);
    });
    
}



function set_field_visibility(frm, fieldname, condition) {
    frm.set_df_property(fieldname, 'hidden', condition ? 0 : 1);
}