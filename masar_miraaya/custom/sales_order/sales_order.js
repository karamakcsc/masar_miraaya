frappe.ui.form.on('Sales Order', {
        onload: function(frm){
            frm.fields_dict['custom_delivery_company'].get_query = function(frm) {
                return {
                    filters: {
                        "custom_is_delivery": 1,
                    }
                };
            };
            FilterPaymentChannel(frm)
        }, 
        setup:function(frm){
            frm.fields_dict['custom_delivery_company'].get_query = function(frm) {
                return {
                    filters: {
                        "custom_is_delivery": 1,
                    }
                };
            };
            FilterPaymentChannel(frm)
        }, 
        refresh:function(frm){
            frm.fields_dict['custom_delivery_company'].get_query = function(frm) {
                return {
                    filters: {
                        "custom_is_delivery": 1,
                    }
                };
            };
            FilterPaymentChannel(frm)
        }
    });



    
function FilterPaymentChannel(frm){
    frm.fields_dict['custom_payment_channels'].grid.get_field('channel_name').get_query = function(doc, cdt, cdn) {
        let channel_names = [];

        if (doc.custom_payment_channels && doc.custom_payment_channels.length) {
            channel_names = doc.custom_payment_channels.map(name => name.channel_name);
        }
        return {
            filters: [
                ["Customer", "disabled", "=", 0],
                ["Customer", "custom_is_payment_channel", "=", 1],
                ["Customer", "name", "not in", channel_names]
            ]
        };
    };
}