// Copyright (c) 2024, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Increment", {
    async employee(frm) {
        if (frm.doc.employee) {
            await fetch_salary_structure(frm);
        }
        frm.trigger("increment_amount");
    },

    async increment_date(frm) {
        if (frm.doc.increment_date) {
            await fetch_salary_structure(frm);
        }
        frm.trigger("increment_amount");
    },

    increment_amount(frm) {
        frm.set_value("revised_salary", frm.doc.current_salary + frm.doc.increment_amount);
    }
});

async function fetch_salary_structure(frm) {
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
