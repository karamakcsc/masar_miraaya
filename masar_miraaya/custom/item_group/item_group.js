frappe.ui.form.on('Item Group', {
    before_save: function(frm){
        frappe.call({
            method:'masar_miraaya.custom.item_group.item_group.check_brands',
            args:{
                name: frm.doc.name,
                parent_item_group_id : frm.doc.custom_parent_item_group_id
            }, 
            callback:function(r) { 
                if(r.message){
                frappe.msgprint(r.message);
                frappe.validated = false;
            }
            }

        })
    }
});