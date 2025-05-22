frappe.ui.form.on("Payment Entry", {
    validate: function(frm) {
        set_magento_id(frm);
    },
    custom_get_magento_id: function(frm) {
        set_magento_id(frm);
    }
});

function set_magento_id(frm) {
    if (frm.doc.references && frm.doc.references.length > 0) {
        frappe.call({
            method: "masar_miraaya.custom.payment_entry.payment_entry.get_magento_id",
            args: {
                pe_doc: frm.doc.name
            },
            callback: function(r) {
                if (r.message) {
                    r.message.forEach(row => {
                        const child = frm.doc.references.find(ref => ref.reference_name === row.reference_name);
                        if (child) {
                            frappe.model.set_value(child.doctype, child.name, "custom_magento_id", row.custom_magento_id);
                        }
                    });
                    frm.refresh_field("references");
                }
            }
        });
    }
}
