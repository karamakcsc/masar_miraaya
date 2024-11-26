frappe.ui.form.on('Pick List', {
    onload: function (frm) {
        hide_create_button(frm);
        create_picked_button(frm);
        create_assigned_button(frm);
    },    
    refresh: function (frm) {
        hide_create_button(frm);
        create_picked_button(frm);
        create_assigned_button(frm);
    },
    setup: function (frm) {
        hide_create_button(frm);
        create_picked_button(frm);
        create_assigned_button(frm);
    }
});


function create_assigned_button(frm) {
    frm.set_df_property("locations", "cannot_add_rows", true);
	frm.set_df_property("locations", "cannot_delete_rows", true);
    
    if (frm.doc.docstatus === 0 && frm.doc.custom_assigned === 0 && frappe.user.has_role('Picker')){
        frm.add_custom_button(__('Assign To Me'), function() {
            frappe.call({
                method: "masar_miraaya.custom.pick_list.pick_list.assign_to_me",
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
function hide_create_button(frm) {
    setTimeout(() => {
        frm.page.wrapper.find('.inner-grcdoup-button[data-label="Create"]').hide();
        frm.page.wrapper.find('.btn.btn-default.ellipsis[data-label="Update%20Current%20Stock"]').hide();
        frm.page.wrapper.find('.inner-group-button:contains("Stock Reservation")').hide();
        }, 5);
}
function create_picked_button(frm) {
    if(frm.doc.docstatus === 1 && frm.doc.custom_packed === 0 && frappe.user.has_role('Dispatcher')) { 
        frm.add_custom_button(__('Packing'), function() {
           frappe.call({
            method:'masar_miraaya.custom.pick_list.pick_list.packing', 
            args:{self: frm.doc},
            callback:function(r){
                frm.refresh_field("custom_packed");
                frm.reload_doc();
            }
           })
        });
    }
}