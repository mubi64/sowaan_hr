// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Arrears Process Setting", {
    example_salary_slip(frm) {
        if (frm.doc.example_salary_slip) {
            frm.set_value("earnings", []);
            frm.set_value("deductions", []);
            frappe.call({
                method: "frappe.client.get",
                args: {
                    doctype: "Salary Slip",
                    name: frm.doc.example_salary_slip,
                },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value("earnings", r.message.earnings.map(row => ({ ...row, amount: 0, name: null })));
                        frm.set_value("deductions", r.message.deductions.map(row => ({ ...row, amount: 0, name: null })));
                        frm.refresh_fields();
                    }
                }
            });
        }
    },
});
