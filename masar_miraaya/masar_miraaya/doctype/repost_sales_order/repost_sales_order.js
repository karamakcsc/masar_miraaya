// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on("Repost Sales Order", {
	refresh(frm) {
        GetSalesOrders(frm);
	},
    onload(frm) {
        GetSalesOrders(frm);
    }, 
    from_date(frm) {
        GetSalesOrders(frm);
    },
    to_date(frm) {
        GetSalesOrders(frm);
    }, 
    repost: function(frm) {
                frappe.call({
                    doc: frm.doc,
                    freeze: true,
                    freeze_message: __('Reposting Sales Orders'),
                    method : 'repost_sales_orders',
                    callback: function(r) {
                        refresh_field('orders');
                    }
                })
    }, 
    status: function(frm) {
        GetSalesOrders(frm);
    },
});

function GetSalesOrders(frm){ 
    if (frm.doc.from_date && frm.doc.to_date) {
        frm.add_custom_button(__("Sales Order"), function(){
            frappe.call({
                doc: frm.doc,
                method : 'get_sales_orders',
                callback: function(r) {
                    refresh_field('orders');
                }
            })
        }, __("Get"));
    }
    frm.fields_dict['orders'].grid.get_field('sales_order').get_query = function() {
        return { 
            filters: [
                ["custom_magento_status", "=", frm.doc.status],
                ["is_group", "=", 0]
            ]
        };
    };
}
