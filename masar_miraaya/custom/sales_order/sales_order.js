frappe.ui.form.on('Sales Order', {
        onload: function(frm){
            frm.fields_dict['custom_delivery_company'].get_query = function(frm) {
                return {
                    filters: {
                        "custom_is_delivery": 1,
                    }
                };
            };
            frm.fields_dict['custom_payment_channels'].grid.get_field('channel_name').get_query = function(doc, cdt, cdn) {
                return {
                    filters: [
                        ["Customer", "disabled", "=", 0],
                        ["Customer", "custom_is_payment_channel", "=", 1]
                    ]
                };
            };
    
        }, 
        setup:function(frm){
            frm.fields_dict['custom_delivery_company'].get_query = function(frm) {
                return {
                    filters: {
                        "custom_is_delivery": 1,
                    }
                };
            };
            frm.fields_dict['custom_payment_channels'].grid.get_field('channel_name').get_query = function(doc, cdt, cdn) {
                return {
                    filters: [
                        ["Customer", "disabled", "=", 0],
                        ["Customer", "custom_is_payment_channel", "=", 1]
                    ]
                };
            };
        }, 
        refresh:function(frm){
            frm.fields_dict['custom_delivery_company'].get_query = function(frm) {
                return {
                    filters: {
                        "custom_is_delivery": 1,
                    }
                };
            };
            frm.fields_dict['custom_payment_channels'].grid.get_field('channel_name').get_query = function(doc, cdt, cdn) {
                return {
                    filters: [
                        ["Customer", "disabled", "=", 0],
                        ["Customer", "custom_is_payment_channel", "=", 1]
                    ]
                };
            };
        }
    });
    