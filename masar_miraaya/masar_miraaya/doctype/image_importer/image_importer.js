// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on("Image Importer", {
	upload: function(frm) {
        frappe.call({
            doc:frm.doc, 
            method:'execute'
        })

	},
});
