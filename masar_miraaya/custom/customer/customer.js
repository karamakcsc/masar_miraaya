frappe.ui.form.on('Customer', {
    setup:function(frm){
        if (frm.is_new()) {
            frm.set_value('custom_customer_id', 0);
        }
    },
    onload:function(frm){
        if (frm.is_new()) {
            frm.set_value('custom_customer_id', 0);
        }
    }
});