// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Sowaan HR Setting", {
	// refresh(frm) {
    // },
    based_on(frm) {
        frm.clear_table("employees");
        frm.clear_table("salary_structures");
        frm.refresh_fields(["employees", "salary_structures"]);
    },
    calculation_method(frm) {
        frm.doc.late_deduction_factor = 0;
        frm.doc.early_deduction_factor = 0;
        frm.doc.half_day_deduction_factor = 0;
    },
    is_late_deduction_applicable(frm) {
        frm.doc.late_salary_component = "";
        frm.doc.late_entry_exemptions = 0;
        frm.doc.late_deduction_factor = 0;

    },
    is_early_deduction_applicable(frm) {
        frm.doc.early_salary_component = "";
        frm.doc.early_exit_exemptions = 0;
        frm.doc.early_deduction_factor = 0;
    },
    is_half_day_deduction_applicable(frm) {
        frm.doc.half_day_salary_component = "";
        frm.doc.half_day_exemptions = 0;
        frm.doc.half_day_deduction_factor = 0;
    },
    
});




// function set_required_fields(frm) {
//     frm.set_df_property('late_salary_component', 'reqd', frm.doc.is_late_deduction_applicable ? 1 : 0);

//     frm.set_df_property('early_salary_component', 'reqd', frm.doc.is_early_deduction_applicable ? 1 : 0);
    
//     frm.set_df_property('half_day_salary_component', 'reqd', frm.doc.is_half_day_deduction_applicable ? 1 : 0);

//     frm.set_df_property('employees', 'reqd', frm.doc.based_on == "Employees" ? 1 : 0);

//     frm.set_df_property('salary_structures', 'reqd', frm.doc.based_on == "Salary Structures" ? 1 : 0);
// }
