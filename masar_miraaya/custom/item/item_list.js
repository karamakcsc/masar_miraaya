frappe.listview_settings['Item'] = {
    onload: function(listview) { 
        listview.page.add_inner_button(__("Sync"), function () {
            frappe.call({
                method: 'masar_miraaya.api_tools.get_magento_products',
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
