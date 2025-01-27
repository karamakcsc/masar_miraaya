// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on("Variant Converter", {
	template_item: function(frm) {
        SetAttributeName(frm);
        // SetAttributeValue(frm);
        
    },
    // refresh: function(frm) {
    //     SetAttributeValue(frm);
    // }
});

frappe.ui.form.on("Variant Converter Item", {
    item_code: function (frm, cdt, cdn) {
        set_read_only(frm, cdt, cdn);
        SetAttributeValue(frm);
    }, 
    // form_render: function (frm, cdt, cdn) {
    //     SetAttributeValue(frm);
    // }, 
});



function SetAttributeName(frm) {
    if (frm.doc.template_item) {
        frm.set_value("color_attr", null);
        frm.set_value("shade_attr", null);
        frm.set_value("size_attr", null);
        frm.set_value("size_ml_attr", null);
        frappe.call({
            doc: frm.doc,
            method: "set_temp_attributes",
            callback: function(r) {
                if (r.message) {
                    const attributes = r.message;
                    attributes.forEach(attr => {
                        console.log(attr);
                        if (attr === "Color"){
                            frm.set_value("color_attr", attr);
                        } else if (attr == "shade"){
                            frm.set_value("shade_attr", attr);
                        } else if (attr == "Size"){
                            frm.set_value("size_attr", attr);
                        } else if (attr == "Size (ml)"){
                            frm.set_value("size_ml_attr", attr);
                        }
                    });
                }
            }
        });
    }
}


function set_read_only(frm, cdt, cdn) {
    let row = frappe.get_doc(cdt, cdn);
    if (frm.doc.color_attr) {
        frm.fields_dict["items"].grid.update_docfield_property("color", "read_only", 0);
    } else {
        frm.fields_dict["items"].grid.update_docfield_property("color", "read_only", 1);
    }

    if (frm.doc.shade_attr) {
        frm.fields_dict["items"].grid.update_docfield_property("shade", "read_only", 0);
    } else {
        frm.fields_dict["items"].grid.update_docfield_property("shade", "read_only", 1);
    }

    if (frm.doc.size_attr) {
        frm.fields_dict["items"].grid.update_docfield_property("size", "read_only", 0);
    } else {
        frm.fields_dict["items"].grid.update_docfield_property("size", "read_only", 1);
    }

    if (frm.doc.size_ml_attr) {
        frm.fields_dict["items"].grid.update_docfield_property("size_ml", "read_only", 0);
    } else {
        frm.fields_dict["items"].grid.update_docfield_property("size_ml", "read_only", 1);
    }

    frm.refresh_field("items");
}

function SetAttributeValue(frm) {
    frappe.call({
        doc: frm.doc,
        method: "get_attributes",
        callback: function (r) {
            const a = r.message;
            frm.fields_dict["items"].grid.update_docfield_property("shade", "options", a.shade);
            frm.fields_dict["items"].grid.update_docfield_property("size", "options", a.size);
            frm.fields_dict["items"].grid.update_docfield_property("size_ml", "options", a.size_ml);
            frm.fields_dict["items"].grid.update_docfield_property("color", "options", a.color);
            frm.refresh_field("items"); 
            }
        })
    }