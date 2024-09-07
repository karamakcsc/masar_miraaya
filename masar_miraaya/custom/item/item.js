frappe.ui.form.on('Item', {
    custom_max_qty: function (frm) {
        if (frm.doc.custom_max_qty) {
            let max_qty = frm.doc.custom_max_qty;

            frappe.call({
                method: "masar_miraaya.custom.item.item.get_values",
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
    },
    // item_group: function (frm) {
    //     if (frm.doc.item_group) {
    //         frappe.call({
    //             method: "masar_miraaya.custom.item.item.get_item_group_id",
    //             args: {
    //                 item_group: frm.doc.item_group,
    //             },
    //             callback: function(r) {
    //                 if (r.message) {
    //                     frm.set_value('custom_item_group_id', r.message);
    //                 }
    //             }
    //         });
    //     }
    // },
    validate: function (frm) {
        if (frm.doc.custom_max_qty) {
            let max_qty = frm.doc.custom_max_qty;

            frappe.call({
                method: "masar_miraaya.custom.item.item.get_values",
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


