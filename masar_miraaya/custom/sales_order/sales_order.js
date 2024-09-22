frappe.ui.form.on('Sales Order', {
    onload: function (frm) {
        delivery_company(frm);
        payment_channel(frm);
    },

    validate: function (frm) {
        delivery_company(frm);
        payment_channel(frm);
    },
    
    refresh: function (frm) {
        delivery_company(frm);
        payment_channel(frm);
    },
    
    setup: function (frm) {
        delivery_company(frm);
        payment_channel(frm);
    }
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
