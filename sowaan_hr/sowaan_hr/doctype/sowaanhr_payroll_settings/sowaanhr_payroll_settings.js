// Copyright (c) 2024, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("SowaanHR Payroll Settings", {
	refresh(frm) {


        frm.set_query('component', 'earning', () => {
            return {
                filters: [
                    ["Salary Component","disabled","=",0],
                    ["Salary Component","type","=","Earning"] ,
                ]
            };
        });

        frm.set_query('component', 'deduction', () => {
            return {
                filters: [
                    ["Salary Component","disabled","=",0],
                    ["Salary Component","type","=","Deduction"] ,
                ]
            };
        });


	},
});
