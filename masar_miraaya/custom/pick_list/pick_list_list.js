frappe.ui.form.on('Pick List', {
    onload: function(frm) {
        if (
            frm.doc.custom_packed === 0 &&
            frappe.user.has_role('Picker') &&
            frm.doc.custom_assigned_to != frappe.session.user
        ) {
            frappe.call({
                method: 'masar_miraaya.custom.pick_list.pick_list.user_validation_picker',
                args: {
                    self: JSON.stringify(frm.doc)
                },
                callback: function(r) {
                    if (!r.exc) {
                        frm.fields_dict.forEach(function(fieldname) {
                            frm.set_df_property(fieldname, 'read_only', 1);
                        });
                        frappe.msgprint(__('This Pick List is assigned to another user and cannot be modified.'));
                    } else {
                        frappe.set_route('List', 'Pick List');
                    }
                }
            });
        }
    }
});
