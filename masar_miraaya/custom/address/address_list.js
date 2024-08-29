// frappe.listview_settings['Address'] = {
//     onload: function(listview) { 
//         listview.page.add_inner_button(__("Sync"), function () {
//             frappe.call({
//                 method: 'masar_miraaya.api.create_customer_address',
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
