frappe.ui.form.on('Material Request', {
    refresh: function (frm) {
        ShowButtons(frm);
    },
    onload: function(frm) {
        ShowButtons(frm);
    },
    setup:function(frm){
        ShowButtons(frm);
    }
    
});
function ShowButtons(frm){
    if (frappe.user.has_role("Fulfillment User") && frm.doc.custom_assigned_to  && frm.doc.custom_assigned_to == frappe.session.user){
        frm.page.wrapper.find('.inner-group-button[data-label="Create"]').show();
    }
    else{
        frm.page.wrapper.find('.inner-group-button[data-label="Create"]').hide();
        create_picked_button(frm);
    }
    
}

function create_picked_button(frm) {
    if(frm.doc.docstatus === 1) { 
        frm.add_custom_button(__('Assign Me'), function() {
            frappe.call({
                method: "masar_miraaya.custom.material_request.material_request.assign_me",
                args:{
                    self : frm.doc,
                },
                callback: function(r) {
                    frm.refresh_field("custom_assigned_to");
                    frm.reload_doc();
                    if (r.message){
                        frm.page.wrapper.find('.inner-group-button[data-label="Create"]').show();
                        }
                }
            })
            
        });
    }
}