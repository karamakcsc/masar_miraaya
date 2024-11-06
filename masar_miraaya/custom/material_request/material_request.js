frappe.ui.form.on('Material Request', {
    refresh: function (frm) {
        create_picked_button(frm);
    },
    onload: function(frm) {
        if (frappe.user.has_role("Carrier")) {
            if (frm.doc.custom_assigned_to && frm.doc.custom_assigned_to !== frappe.session.user) {
                frappe.throw("You are not assigned to this doc.");
                // frappe.set_route("List", "Material Request");
 
            }
        }
    }
    
});


function create_picked_button(frm) {
    if(frm.doc.docstatus === 1) { 
        frm.add_custom_button(__('Assign Me'), function() {
            frappe.call({
                method: "masar_miraaya.custom.material_request.material_request.role_validate",
                args:{
                    self : frm.doc,
                },
                callback: function(r) {
                    frm.refresh_field("custom_assigned_to");
                    frm.reload_doc();
                }
            })
            
        });
    }
}