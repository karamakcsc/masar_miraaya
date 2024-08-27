frappe.listview_settings['Customer'] = {
    onload: function(listview) { 
        listview.page.add_inner_button(__("Sync"), function () {
            frappe.call({
                method: 'masar_miraaya.api.get_magento_customers',
                callback: function(response) {
                    frappe.msgprint(__('Sync Complete.'));
                },
            });
            frappe.show_alert({
                message: __('Sync has started in the background.'),
                indicator: 'green',
            });
        });
    }
};
