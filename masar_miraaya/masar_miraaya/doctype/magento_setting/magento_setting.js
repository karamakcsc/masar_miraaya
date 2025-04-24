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
    create_mag_auth_wallet: function (frm) {
        frappe.call({
            method: "masar_miraaya.api.create_magento_auth_wallet",
            callback: function(r) {
                if (r.message) {
                    frm.set_value('auth_wallet', r.message);
                }
            }
        });
    },
    create_magento_admin_prod_auth: function (frm) {
        frappe.call({
            method: "masar_miraaya.api.create_magento_auth_webhook",
            callback: function(r) {
                if (r.message) {
                    frm.set_value('magento_admin_prod_auth', r.message);
                }
            }
        });
    },
    create_magento_customer_prod_auth: function (frm) {
        frappe.call({
            method: "masar_miraaya.api.create_magento_auth_wallet_webhook",
            callback: function(r) {
                if (r.message) {
                    frm.set_value('magento_cust_prod_auth', r.message);
                }
            }
        });
    },
    onload: function (frm) {
        if(frappe.session.user != 'Administrator') {
            frm.toggle_display("magento_admin_details_section", false);
            frm.toggle_display("magento_wallet_details_section", false);
        }
    },
    setup: function (frm) {
        if(frappe.session.user != 'Administrator') {
            frm.toggle_display("magento_admin_details_section", false);
            frm.toggle_display("magento_wallet_details_section", false);
        }
    },
    refresh: function (frm) {
        if(frappe.session.user != 'Administrator') {
            frm.toggle_display("magento_admin_details_section", false);
            frm.toggle_display("magento_wallet_details_section", false);
        }
    },
    // update_images: function (frm) {
    //     update_images(frm);
    // }
});


// function update_images(frm) {
//     frappe.call({
//         doc: frm.doc,
//         method: "update_images",
//         callback: function (r) {
//             if (r.message) {
//                 frappe.show_alert({
//                     message: __('Images updated successfully'),
//                     indicator: 'green'
//                 });
//             }
//         }
//     });
// }