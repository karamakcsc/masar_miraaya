frappe.ui.form.on('Customer', {
    setup:function(frm){
        if (frm.is_new()) {
            frm.set_value('custom_customer_id', 0);
        }
        set_wallet_balance(frm);
    },
    onload:function(frm){
        set_wallet_balance(frm);
        if (frm.is_new()) {
            frm.set_value('custom_customer_id', 0);
        }
    },
    refresh: function(frm){
        set_wallet_balance(frm);
    }
});

// Get The Balance For Customer From Magento
function set_wallet_balance(frm) {
    if (frm.doc.custom_is_publish === 1) {
		frappe.call({
			method: 'masar_miraaya.custom.customer.customer.cust_wallet_balance',
            args: {
                customer_id: frm.doc.name,
                magento_id: frm.doc.custom_customer_id
            },
			callback: function(r) {
                frm.doc.custom_lp_balance = r.message;
				frm.refresh_field("custom_lp_balance");
			}
		});
	}
}