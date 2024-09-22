frappe.ui.form.on('Wallet Top-up', {
    customer: function (frm) {
        update_sales_order_filter(frm);
    },

    onload: function (frm) {
        setQueryFilters(frm);
        if (frm.doc.customer) {
            update_sales_order_filter(frm);
        }
    },

    validate: function (frm) {
        update_sales_order_filter(frm);
    },
    refresh:function(frm){
        setQueryFilters(frm);
    },
    setup: function (frm) {
        setQueryFilters(frm);
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
                    } else {
                        frm.clear_table('items');
                        frm.refresh_field('items');
                    }
                }
            });
        } else {
            frm.clear_table('items');
            frm.refresh_field('items');
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


function setQueryFilters(frm) {
    frm.fields_dict['digital_wallet'].get_query = function(frm) {
        return {
            filters: {
                "custom_is_digital_wallet": 1,
                "is_frozen": 0,
                "disabled": 0
            }
        };
    };
    
    frm.fields_dict['wallet_adjustment_account'].get_query = function(frm) {
        return {
            filters: {
                "is_group": 0
            }
        };
    };
    
    frm.fields_dict['customer'].get_query = function(frm) {
        return {
            filters: {
                "custom_is_digital_wallet": 0,
                "custom_is_payment_channel": 0,
                "custom_is_delivery": 0,
                "is_frozen": 0,
                "disabled": 0
            }
        };
    };
}