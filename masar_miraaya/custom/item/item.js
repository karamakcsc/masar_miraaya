frappe.ui.form.on('Item', {
    custom_max_qty: function (frm) {
        GetMaxQty(frm);
    },
    validate: function (frm) {
        GetMaxQty(frm);
    }, 
    onload: function(frm){
        frm.fields_dict['item_group'].get_query = function(frm) {
            return {
                filters: {
                    "is_group": 0,
                }
            };
        };

    }, 
    setup:function(frm){
        frm.fields_dict['item_group'].get_query = function(frm) {
            return {
                filters: {
                    "is_group": 0,
                }
            };
        };
    }, 
    refresh:function(frm){
        frm.fields_dict['item_group'].get_query = function(frm) {
            return {
                filters: {
                    "is_group": 0,
                }
            };
        };
    }
});
function GetMaxQty(frm){
    if (frm.doc.custom_max_qty) {
        let max_qty = frm.doc.custom_max_qty;

        frappe.call({
            method: "masar_miraaya.custom.item.item.get_actual_qty_value",
            args: {
                item_code: frm.doc.name,
            },
            callback: function(r) {
                if (r.message) {
                    let actual_qty = r.message;
                    let reorder_qty = max_qty - actual_qty;

                    frm.doc.reorder_levels.forEach(function(row) {
                        frappe.model.set_value(row.doctype, row.name, "warehouse_reorder_qty", reorder_qty);
                    });

                    frm.refresh_field('reorder_levels');
                }
            }
        });
}
}