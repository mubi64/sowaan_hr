// Copyright (c) 2024, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Increment", {
    refresh(frm) {

    },
    async employee(frm) {
        if (frm.doc.employee) {
            await frappe.call({
                method: "get_structure_asignment",
                doc: frm.doc,
                callback: function (r) {
                    if (r.message) {
                        frm.set_value("current_salary", r.message.base);
                    }
                }
            });
        }
        if (frm.doc.increment_amount) {
            frm.trigger("increment_amount");
        }
    },
    increment_amount(frm) {
        if (frm.doc.increment_amount && frm.doc.employee) {
            frm.set_value("revised_salary", frm.doc.current_salary + frm.doc.increment_amount);
        }
    }
});
