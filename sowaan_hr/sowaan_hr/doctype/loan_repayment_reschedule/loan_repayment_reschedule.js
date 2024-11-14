// Copyright (c) 2024, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Loan Repayment Reschedule", {
	// refresh(frm) {

	// },

    applicant : function(frm)
    {


        if (frm.doc.applicant_type == 'Employee') {
                
            frm.set_value("loan", "");
            frm.set_query("loan", function () {
                return {
                        filters: [
                            ["Loan", "docstatus", "=", 1] ,
                            ["Loan", "applicant", "=", frm.doc.applicant] ,
                        ],
                };
            });
            
        }
    
    }


});
