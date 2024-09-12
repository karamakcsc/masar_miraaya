frappe.ui.form.on('Company', {
    onload: function(frm){
        frm.fields_dict['custom_cost_of_delivery'].get_query = function(frm) {
            return {
                filters: {
                    "is_group": 0,
                }
            };
        };
    }, 
    setup:function(frm){
        frm.fields_dict['custom_cost_of_delivery'].get_query = function(frm) {
            return {
                filters: {
                    "is_group": 0,
                }
            };
        };
    }, 
    refresh:function(frm){
        frm.fields_dict['custom_cost_of_delivery'].get_query = function(frm) {
            return {
                filters: {
                    "is_group": 0,
                }
            };
        };
    }
});
