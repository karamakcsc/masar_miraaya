frappe.ui.form.on('Item Group', {
    parent_item_group: function (frm) {
        if (frm.doc.parent_item_group) {
            frappe.call({
                method: "masar_miraaya.custom.item_group.item_group.get_parent_item_group_id",
                args: {
                    parent_id: frm.doc.parent_item_group,
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('custom_parent_item_group_id', r.message);
                    }
                }
            });
        }
    }
});