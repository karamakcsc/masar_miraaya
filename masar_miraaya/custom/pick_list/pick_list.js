frappe.ui.form.on('Pick List', {
    onload: function (frm) {
        hide_create_button(frm);
    },    
    refresh: function (frm) {
        hide_create_button(frm);
        create_picked_button(frm);
    },
    setup: function (frm) {
        hide_create_button(frm);
    }
});

function hide_create_button(frm) {
    setTimeout(() => {
        frm.page.wrapper.find('.inner-group-button[data-label="Create"]').hide();
        frm.page.wrapper.find('.btn.btn-default.ellipsis[data-label="Update%20Current%20Stock"]').hide();
    }, 5);
}



function create_picked_button(frm) {
    if(frm.doc.docstatus === 1) { 
        frm.add_custom_button(__('Picking'), function() {
            frappe
			.xcall("masar_miraaya.custom.pick_list.pick_list.new_stock_entry", {
				pick_list: frm.doc,
			})
			.then((stock_entry) => {
				frappe.model.sync(stock_entry);
				frappe.set_route("Form", "Stock Entry", stock_entry.name);
			});
        });
    }
}