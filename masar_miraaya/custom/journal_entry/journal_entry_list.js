// frappe.listview_settings['Journal Entry'] = {
//     onload : function(listview) {
//         frappe.route_options = {
//             "Reference Doctype": ""
//           };
//         listview.refresh();
//     }
// };

frappe.listview_settings['Journal Entry'] = {
    onload: function(listview) {
        setTimeout(() => {
            $('.filter-x-button').click();
        }, 50);
    }
};