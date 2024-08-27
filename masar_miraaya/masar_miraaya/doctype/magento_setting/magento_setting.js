// Copyright (c) 2024, KCSC and contributors
// For license information, please see license.txt


frappe.ui.form.on('Magento Setting', {
    create_magento_auth: function (frm) {
            frappe.call({
                method: "masar_miraaya.api.create_magento_auth",
                callback: function(r) {
                    if (r.message) {
                        // frappe.msgprint(r.message);
                        frm.set_value('magento_auth', r.message);
                    }
                }
            });
        }
    
});
