frappe.listview_settings['Item Attribute'] = {
    onload: function(listview) { 
        listview.page.add_inner_button(__("Sync Color"), function () {
            frappe.call({
                method: 'masar_miraaya.api.get_magento_colors',
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
        });

        listview.page.add_inner_button(__("Sync Shade"), function () {
            frappe.call({
                method: 'masar_miraaya.api.get_magento_shades',
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
        });

        listview.page.add_inner_button(__("Sync Size"), function () {
            frappe.call({
                method: 'masar_miraaya.api.get_magento_size',
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
        });

        listview.page.add_inner_button(__("Sync Size_Ml"), function () {
            frappe.call({
                method: 'masar_miraaya.api.get_magento_size_ml',
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
        });
    }
};
