// Copyright (c) 2024, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on("Picking Area", {
	refresh: function(frm) {
            if(frm.doc.__islocal != 1 && frm.doc.docstatus === 0) { 
                frm.add_custom_button(__('Get Items'), function() {
                    frappe.call({
                        doc: frm.doc,
                        method: "fetch_child_items",
                        callback: function(r) {
                            frm.refresh_field("items");
                        }
                    });
                });
            }
	},
});
