frappe.ui.form.on('Salary Slip', {
    custom_adjust_negative_salary(frm) {
        frm.set_value('custom_check_adjustment', frm.doc.custom_adjust_negative_salary ? 1 : 0);
    },
    refresh(frm) {
        get_hr_settings(frm);
    },
    validate(frm) {
        get_hr_settings(frm);
    }
});

function get_hr_settings(frm) {
    if (!frm.doc.employee || !frm.doc.salary_structure) {
        return;
    }
    frappe.call({
        method: "sowaan_hr.sowaan_hr.events.Salary_slip.get_deduction_parent",
        args: {
            employee: frm.doc.employee,
            salary_structure: frm.doc.salary_structure
        },
        callback: function(response) {
            let parent_to_use = response.message;
            if (!parent_to_use) {                
                set_field_visibility(frm, 'custom_late_entry_minutes', 0);
                set_field_visibility(frm, 'custom_early_exit_minutes', 0);
                set_field_visibility(frm, 'custom_late_entry_counts', 0);
                set_field_visibility(frm, 'custom_early_exit_counts', 0);
                set_field_visibility(frm, 'custom_total_half_days', 0);
                set_field_visibility(frm, 'custom_deductible_late_entry_counts', 0);
                set_field_visibility(frm, 'custom_deductible_early_exit_counts', 0);
                set_field_visibility(frm, 'custom_deductible_half_days', 0);
                return;
            }
            frappe.db.get_value('Sowaan HR Setting', {'name': parent_to_use}, 
                ['is_late_deduction_applicable', 'is_early_deduction_applicable', 'is_half_day_deduction_applicable', 'calculation_method']
            ).then(r => {
                if (r && r.message) {
                    // set_field_visibility(frm, 'custom_late_entry_minutes', r.message.is_late_deduction_applicable);
                    // set_field_visibility(frm, 'custom_early_exit_minutes', r.message.is_early_deduction_applicable);
                    // set_field_visibility(frm, 'custom_total_half_days', r.message.is_half_day_deduction_applicable);

                    const method = r.message.calculation_method;

                    // Late deduction visibility
                    if (r.message.is_late_deduction_applicable) {
                        set_field_visibility(frm, 'custom_late_entry_minutes', method === 'Minutes');
                        set_field_visibility(frm, 'custom_late_entry_counts', method === 'Counts');
                        set_field_visibility(frm, 'custom_deductible_late_entry_counts', method === 'Counts');
                    } else {
                        set_field_visibility(frm, 'custom_late_entry_minutes', 0);
                        set_field_visibility(frm, 'custom_late_entry_counts', 0);
                        set_field_visibility(frm, 'custom_deductible_late_entry_counts', 0);
                    }

                    // Early deduction visibility
                    if (r.message.is_early_deduction_applicable) {
                        set_field_visibility(frm, 'custom_early_exit_minutes', method === 'Minutes');
                        set_field_visibility(frm, 'custom_early_exit_counts', method === 'Counts');
                        set_field_visibility(frm, 'custom_deductible_early_exit_counts', method === 'Counts');
                    } else {
                        set_field_visibility(frm, 'custom_early_exit_minutes', 0);
                        set_field_visibility(frm, 'custom_early_exit_counts', 0);
                        set_field_visibility(frm, 'custom_deductible_early_exit_counts', 0);
                    }

                    // Half-day deduction visibility
                    if (r.message.is_early_deduction_applicable) {
                        set_field_visibility(frm, 'custom_total_half_days', r.message.is_half_day_deduction_applicable);
                        set_field_visibility(frm, 'custom_deductible_half_days', r.message.is_half_day_deduction_applicable);
                    } else {
                        set_field_visibility(frm, 'custom_total_half_days', 0);
                        set_field_visibility(frm, 'custom_deductible_half_days', 0);
                    }
                }
            });
        }
    });
}

function set_field_visibility(frm, fieldname, condition) {
    frm.set_df_property(fieldname, 'hidden', condition ? 0 : 1);
}
