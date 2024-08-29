// Copyright (c) 2024, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on('Magento Setting', {
    create_magento_auth: function (frm) {
        frappe.call({
            method: "masar_miraaya.api.create_magento_auth",
            callback: function(r) {
                if (r.message) {
                    frm.set_value('magento_auth', r.message);
                }
            }
        });
    },
    onload: function (frm) {
        if(frappe.session.user != 'Administrator') {
            frm.toggle_display("magento_admin_details_section", false);
        }
    },
    setup: function (frm) {
        if(frappe.session.user != 'Administrator') {
            frm.toggle_display("magento_admin_details_section", false);
        }
    },
    refresh: function (frm) {
        if(frappe.session.user != 'Administrator') {
            frm.toggle_display("magento_admin_details_section", false);
        }
    }
});