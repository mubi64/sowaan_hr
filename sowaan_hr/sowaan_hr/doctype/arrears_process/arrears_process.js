// Copyright (c) 2024, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Arrears Process", {
    refresh(frm) {
        if (frm.doc.a_p_earnings.length === 0 && frm.doc.a_p_deductions.length === 0) {
            frappe.call({
                method: "frappe.client.get",
                args: {
                    doctype: "Arrears Process Setting",
                },
                callback: function (r) {
                    if (r.message) {
                        for (let i = 0; i < r.message.earnings.length; i++) {
                            const ele = r.message.earnings[i];
                            let row = frappe.model.add_child(frm.doc, "Arrears Process Earning", "a_p_earnings");
                            row.salary_component = ele.salary_component;
                            row.amount = 0;
                        }
                        for (let i = 0; i < r.message.deductions.length; i++) {
                            const ele = r.message.deductions[i];
                            let row = frappe.model.add_child(frm.doc, "Arrears Process Deduction", "a_p_deductions");
                            row.salary_component = ele.salary_component;
                            row.amount = 0;
                        }
                        frm.refresh_fields();
                    }
                }
            });
        }
    },
});
