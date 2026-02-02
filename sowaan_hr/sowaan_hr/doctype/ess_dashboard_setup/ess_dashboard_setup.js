// 🔹 Child table row events
frappe.ui.form.on("ESS Dashboard Expiry Config", {

    ref_doctype(frm, cdt, cdn) {
        populate_expiry_field_for_row(frm, locals[cdt][cdn]);
    },

    is_child_table(frm, cdt, cdn) {
        populate_expiry_field_for_row(frm, locals[cdt][cdn]);
    },

    child_table(frm, cdt, cdn) {
        populate_expiry_field_for_row(frm, locals[cdt][cdn]);
    }
});


// ---------------------------
// Populate expiry_field options for a child row (ESS Dashboard)
// ---------------------------
function populate_expiry_field_for_row(frm, row) {
    if (!row.ref_doctype) return;

    const cdt = row.doctype;
    const cdn = row.name;
    console.log("Populating expiry_field for row:", row);

    const selected_value = row.expiry_field;

    

    const target_doctype = row.is_child_table
        ? row.child_table
        : row.ref_doctype;

    if (!target_doctype) return;

    frappe.call({
        method: "sowaan_hr.sowaan_hr.doctype.ess_dashboard_setup.ess_dashboard_setup.get_expiry_fields",
        args: { doctype: target_doctype },
        callback(r) {
            if (!r.message) return;

            // 🔹 Use fieldname::label so label is shown
            const options = [
                "",
                ...r.message.map(f => f.label)
            ];


            const grid = frm.fields_dict.expiry_configurations?.grid;
            if (!grid) return;

            const grid_row = grid.grid_rows_by_docname[row.name];
            if (!grid_row) return;

            const waitForField = () => {
            let ctrl = null;

            try {
                ctrl = grid_row.get_field("expiry_field");
            } catch (e) {
                setTimeout(waitForField, 50);
                return;
            }

            if (!ctrl) {
                setTimeout(waitForField, 50);
                return;
            }

            ctrl.df.options = options.join("\n");
            ctrl.refresh();
        };

            waitForField();
        }
    });
}


frappe.ui.form.on("ESS Dashboard Setup", {
    refresh(frm) {
        if (!frm.doc.expiry_configurations) return;

        frm.doc.expiry_configurations.forEach(row => {
            populate_expiry_field_for_row(frm, row);
        });
    }
});
