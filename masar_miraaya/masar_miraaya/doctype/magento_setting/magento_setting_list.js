// frappe.listview_settings['Magento Setting'] = {
//     onload: function(listview) { 
//         listview.page.add_inner_button(__("Create Magento Auth"), function () {
//             frappe.call({
//                 method: 'masar_miraaya.api.create_magento_auth',
//                 callback: function(response) {
//                     frappe.msgprint(__('Sync Complete.'));
//                 },
//             });
//             frappe.show_alert({
//                 message: __('Sync has started in the background.'),
//                 indicator: 'green',
//             });
//         });
//     }
// };
