frappe.listview_settings['Brand'] = {
    onload: function(listview) { 
        listview.page.add_inner_button(__("Sync"), function () {
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
        });
    }
};