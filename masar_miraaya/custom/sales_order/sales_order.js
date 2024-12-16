frappe.ui.form.on('Sales Order', {
    onload: function (frm) {
        delivery_company(frm);
        payment_channel(frm);
        set_doctype_read_only(frm);
    },    
    refresh: function (frm) {
        delivery_company(frm);
        payment_channel(frm);
        set_doctype_read_only(frm);
    },
    setup: function (frm) {
        delivery_company(frm);
        payment_channel(frm);
        set_doctype_read_only(frm);
    },
    custom_cash_on_delivery_amount:function(frm){
        GetTotalAmount(frm);
    },
    custom_payment_channel_amount:function(frm){
        GetTotalAmount(frm);
    }, 
    custom_is_cash_on_delivery: function(frm){
        if (frm.doc.custom_is_cash_on_delivery === 0 ){
        frm.set_value("custom_cash_on_delivery_amount", 0);
        frm.refresh_field("custom_cash_on_delivery_amount");
        }
    }
});
frappe.ui.form.on("Payment Channel Details", "amount", function(frm, cdt, cdn) {
    frappe.call({
        method : 'masar_miraaya.custom.sales_order.sales_order.get_payment_channel_amount',
        args: {
            child: frm.doc.custom_payment_channels
        },
        callback: function(r){
            frm.set_value("custom_payment_channel_amount", r.message);
            frm.refresh_field("custom_payment_channel_amount");
        }

    })

});
function delivery_company(frm) {
    frm.fields_dict['custom_delivery_company'].get_query = function() {
        return {
            filters: {
                "custom_is_delivery": 1,
                "is_frozen": 0,
                "disabled": 0
            }
        };
    };
}
function payment_channel(frm) {
    frm.fields_dict['custom_payment_channels'].grid.get_field('channel').get_query = function(doc) {
        let channel_names = [];

        if (doc.custom_payment_channels && doc.custom_payment_channels.length) {
            channel_names = doc.custom_payment_channels.map(row => row.channel_name);
        }

        return {
            filters: [
                ["Customer", "disabled", "=", 0],
                ["Customer","is_frozen","=", 0],
                ["Customer", "custom_is_payment_channel", "=", 1],
                ["Customer", "name", "not in", channel_names]
            ]
        };
    };
}
function GetTotalAmount(frm) {
    var totalAmount = 0;
    if (frm.doc.custom_cash_on_delivery_amount) {
        totalAmount += frm.doc.custom_cash_on_delivery_amount;
    }
    if (frm.doc.custom_payment_channel_amount) {
        totalAmount += frm.doc.custom_payment_channel_amount;
    }
    frm.doc.custom_total_amount = totalAmount;
    frm.set_value("custom_total_amount", totalAmount);
    frm.refresh_field("custom_total_amount");
}


function set_doctype_read_only(frm) {
    if (frappe.session.user !== 'Administrator'){
        if (frappe.user.has_role('Picker') || frappe.user.has_role('Dispatcher')) {
            frm.set_read_only(true);
        }

        if (frm.doc.amended_from) {
            frm.set_df_property('apply_discount_on', 'read_only', 1);   // Additional Discount Section Read Only
            frm.set_df_property('additional_discount_percentage', 'read_only', 1);
            frm.set_df_property('base_discount_amount', 'read_only', 1);
            frm.set_df_property('discount_amount', 'read_only', 1);
            frm.set_df_property('coupon_code', 'read_only', 1); 
        }
    }
}