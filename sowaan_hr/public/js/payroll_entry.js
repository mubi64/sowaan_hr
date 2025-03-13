// Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

var in_progress = false;

frappe.provide("erpnext.accounts.dimensions");

frappe.ui.form.on("Payroll Entry", {
  create_salary_slips: function (frm) {
    frm.call({
      doc: frm.doc,
      method: "run_doc_method",
      args: {
        method: "create_salary_slips",
        dt: "Payroll Entry",
        dn: frm.doc.name,
      },
    });
  },

  add_bank_entry_button: function (frm) {
    frm.call("has_bank_entries").then((r) => {
      if (!r.message.has_bank_entries) {
        frm
          .add_custom_button(__("Make Bank Entry"), function () {
            make_bank_entry(frm);
          })
          .addClass("btn-primary");
      } else if (!r.message.has_bank_entries_for_withheld_salaries) {
        frm
          .add_custom_button(
            __("Release Withheld Salaries"),
            async function () {
              // show dialog
              // make_bank_entry(frm, (for_withheld_salaries = 1));
              held_employees = frm.doc.employees.filter(
                (e) => e.is_salary_withheld
              );
              if (held_employees.length > 0) {
                let d = new frappe.ui.Dialog({
                  title: __("Select Employees"),
                  fields: [
                    {
                      label: "Employees",
                      fieldname: "hold_employees",
                      fieldtype: "Table",
                      cannot_add_rows: true,
                      cannot_delete_rows: true,
                      in_place_edit: true,
                      data: held_employees,
                      fields: [
                        {
                          fieldname: "employee",
                          fieldtype: "Link",
                          in_list_view: 1,
                          options: "Employee",
                          label: "Employee",
                        },
                        {
                          fieldname: "employee_name",
                          fieldtype: "Data",
                          in_list_view: 1,
                          label: "Employee Name",
                        },
                        {
                          fieldname: "is_salary_withheld",
                          fieldtype: "Check",
                          in_list_view: 1,
                          label: "Is Salary Withheld",
                        },
                      ],
                    },
                  ],
                  primary_action_label: "Release",
                  primary_action(res) {
                    let selectedEmployee = res.hold_employees.filter((emp) => {
                      if (emp.__checked === 1) {
                        return emp;
                      }
                    });

                    if (selectedEmployee.length > 0) {
                      released_salary(frm, selectedEmployee, 1);
                    } else {
                      frappe.show_alert(
                        {
                          message: __("Pleace select the Employee"),
                          indicator: "red",
                        },
                        5
                      );
                    }
                  },
                });
                d.show();
              } else {
                // show message no employee salary is hold
                frappe.msgprint(__("All employee salary is cleared"));
              }
            }
          )
          .addClass("btn-primary");
      }
      if (!r.message.has_bank_entries_and_withheld_salaries) {
        frm
          .add_custom_button(
            __("Release Withheld Salaries"),
            async function () {
              // show dialog
              // make_bank_entry(frm, (for_withheld_salaries = 1));
              held_employees = frm.doc.employees.filter(
                (e) => e.is_salary_withheld
              );
              if (held_employees.length > 0) {
                let d = new frappe.ui.Dialog({
                  title: __("Select Employees"),
                  fields: [
                    {
                      label: "Employees",
                      fieldname: "hold_employees",
                      fieldtype: "Table",
                      cannot_add_rows: true,
                      cannot_delete_rows: true,
                      in_place_edit: true,
                      data: held_employees,
                      fields: [
                        {
                          fieldname: "employee",
                          fieldtype: "Link",
                          in_list_view: 1,
                          options: "Employee",
                          label: "Employee",
                        },
                        {
                          fieldname: "employee_name",
                          fieldtype: "Data",
                          in_list_view: 1,
                          label: "Employee Name",
                        },
                        {
                          fieldname: "is_salary_withheld",
                          fieldtype: "Check",
                          in_list_view: 1,
                          label: "Is Salary Withheld",
                        },
                      ],
                    },
                  ],
                  primary_action_label: "Release",
                  primary_action(res) {
                    let selectedEmployee = res.hold_employees.filter((emp) => {
                      if (emp.__checked === 1) {
                        return emp;
                      }
                    });

                    if (selectedEmployee.length > 0) {
                      released_salary(frm, selectedEmployee, 1);
                    } else {
                      frappe.show_alert(
                        {
                          message: __("Pleace select the Employee"),
                          indicator: "red",
                        },
                        5
                      );
                    }
                  },
                });
                d.show();
              } else {
                // show message no employee salary is hold
                frappe.msgprint(__("All employee salary is cleared"));
              }
            }
          )
          .addClass("btn-primary");
      }
    });
  },
});

let released_salary = function (frm, employees, for_withheld_salaries = 0) {
  const doc = frm.doc;
  const employeesList = [...new Set(employees.map((ele) => ele.employee))];

  if (doc.payment_account) {
    return frappe.call({
      method: "run_doc_method",
      args: {
        method: "released_salary",
        dt: "Payroll Entry",
        dn: frm.doc.name,
        args: {
          employees: employeesList,
          for_withheld_salaries: for_withheld_salaries,
        },
      },
      callback: function () {
        frappe.set_route("List", "Journal Entry", {
          "Journal Entry Account.reference_name": frm.doc.name,
        });
      },
      freeze: true,
      freeze_message: __("Creating Payment Entries......"),
    });
  } else {
    frappe.msgprint(__("Payment Account is mandatory"));
    frm.scroll_to_field("payment_account");
  }
};
