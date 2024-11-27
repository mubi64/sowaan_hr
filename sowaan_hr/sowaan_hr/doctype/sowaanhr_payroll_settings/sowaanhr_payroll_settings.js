// Copyright (c) 2024, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("SowaanHR Payroll Settings", {
	refresh(frm) {


        frm.set_query("negative_salary_adjustment_component", function () {
            return {
                    filters: [
                        ["Salary Component", "type", "=", "Earning"] ,
                    ],
            };
        });


        frm.set_query("negative_salary_repayment_component_copy", function () {
            return {
                    filters: [
                        ["Salary Component", "type", "=", "Deduction"] ,
                    ],
            };
        });

	},
});
