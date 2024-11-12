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
        // create_picked_button(frm);
    }
    
}
