frappe.ui.form.on('Customer', {
    customer_group: function (frm) {
        if (frm.doc.customer_group) {
            frappe.call({
                method: "masar_miraaya.custom.customer.customer.get_customer_group_id",
                args: {
                    group_id: frm.doc.customer_group,
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('custom_customer_group_id', r.message);
                    }
                }
            });
        }
    }
});