// Copyright (c) 2024, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on("Magento Sync", {
	brand:function(frm) {
        frappe.call({
            method: 'masar_miraaya.api.get_magento_brand',
            freeze: true,
            freeze_message: 'Please Wait .....',
            callback: function(response) {
                frappe.msgprint(__(response.message));
            },
        });
        frappe.show_alert({
            message: __('Sync has started in the background.'),
            indicator: 'green',
        });

	},
    customer: function(frm){
        frappe.call({
            method: 'masar_miraaya.api.get_magento_customers',
            freeze: true,
            freeze_message: 'Please Wait .....',
            callback: function(response) {
                frappe.msgprint(__(response.message));
            },
        });
        frappe.show_alert({
            message: __('Sync has started in the background.'),
            indicator: 'green',
        });
    },
    customer_group: function(frm){
        frappe.call({
            method: 'masar_miraaya.api.get_customer_group',
            freeze: true,
            freeze_message: 'Please Wait .....',
            callback: function(response) {
                frappe.msgprint(__(response.message));
            },
        });
        frappe.show_alert({
            message: __('Sync has started in the background.'),
            indicator: 'green',
        });
    },
    item:function(frm){
        frappe.call({
            method: 'masar_miraaya.api.sync_magento_products',
            freeze: true,
            freeze_message: 'Please Wait .....',
            callback: function(response) {
                frappe.msgprint(__(response.message));
            },
        });
        frappe.show_alert({
            message: __('Sync has started in the background.'),
            indicator: 'green',
        });
    },
    item_attributes:function(frm){
        frappe.call({
            method: 'masar_miraaya.api.get_magento_item_attributes',
            freeze: true,
            freeze_message: 'Please Wait .....',
            callback: function(response) {
                frappe.msgprint(__(response.message));
            },
        });
        frappe.show_alert({
            message: __('Sync has started in the background.'),
            indicator: 'green',
        });
    },
    item_group:function(frm){
        frappe.call({
            method: 'masar_miraaya.api.create_item_group',
            freeze: true,
            freeze_message: 'Please Wait .....',
            callback: function(response) {
                frappe.msgprint(__('Sync Complete.'));
            },
        });
        frappe.show_alert({
            message: __('Sync has started in the background.'),
            indicator: 'green',
        });
    }
});
