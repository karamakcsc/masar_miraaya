frappe.ui.form.on('Item', {
    // custom_max_qty: function (frm) {
    //     GetMaxQty(frm);
    // },
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

function GetMaxQty(frm) {
    if (frm.doc.reorder_levels && frm.doc.reorder_levels.length > 0) {
        frappe.call({
            method: "masar_miraaya.custom.item.item.get_actual_qty_value",
            args: {
                item_code: frm.doc.name,
            },
            callback: function(r) {
                if (r.message) {
                    let actual_qty = r.message;
                    frm.doc.reorder_levels.forEach(function(row) {
                        let max_qty = row.custom_max_qty || 0;
                        let reorder_qty = max_qty - actual_qty;
                        if (reorder_qty <= 0) {
                            reorder_qty = 0;
                        }
                        frappe.model.set_value(row.doctype, row.name, "warehouse_reorder_qty", reorder_qty);
                    });

                    frm.refresh_field('reorder_levels');
                }
            }
        });
    }
}