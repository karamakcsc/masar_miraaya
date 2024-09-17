// Copyright (c) 2024, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on('Wallet Top-up', {
    customer: function (frm) {
        update_sales_order_filter(frm);
    },

    onload: function (frm) {
        if (frm.doc.customer) {
            update_sales_order_filter(frm);
        }
    },

    validate: function (frm) {
        update_sales_order_filter(frm);
    },

    setup: function (frm) {
        update_sales_order_filter(frm);
    },

    sales_order_no: function (frm) {
        if (frm.doc.sales_order_no) {
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Sales Order',
                    name: frm.doc.sales_order_no
                },
                callback: function (response) {
                    let sales_order = response.message;
                    if (sales_order) {
                        frm.clear_table('items');
                        sales_order.items.forEach(item => {
                            let child = frm.add_child('items');
                            child.item_code = item.item_code;
                            child.qty = item.qty;
                            child.rate = item.rate;
                            child.amount = item.amount;
                        });
                        frm.refresh_field('items');
                    }
                }
            });
        }
    }
});

function update_sales_order_filter(frm) {
    let customer = frm.doc.customer;

    frm.set_query('sales_order_no', function () {
        return {
            filters: {
                'customer': customer,
                'docstatus': 1
            }
        };
    });
}

function toggle_series_field(frm) {
    if (frm.doc.transaction_type === 'Gift Card') {
        frm.toggle_display('series', false);
    } else {
        frm.toggle_display('series', true);
    }
}