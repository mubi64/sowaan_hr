

frappe.ui.form.on('Salary Slip', {
	
    custom_adjust_negative_salary(frm) {
        if (frm.doc.custom_adjust_negative_salary) {
            frm.set_value('custom_check_adjustment',1);
        }
        else {
            frm.set_value('custom_check_adjustment',0);
        }
    },
});