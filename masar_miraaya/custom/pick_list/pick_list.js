frappe.ui.form.on('Pick List', {
    onload: function (frm) {
        hide_create_button(frm);
        create_picked_button(frm);
    },    
    refresh: function (frm) {
        hide_create_button(frm);
        create_picked_button(frm);
    },
    setup: function (frm) {
        hide_create_button(frm);
        create_picked_button(frm);
    }
});

function hide_create_button(frm) {
    setTimeout(() => {
        frm.page.wrapper.find('.inner-group-button[data-label="Create"]').hide();
        frm.page.wrapper.find('.btn.btn-default.ellipsis[data-label="Update%20Current%20Stock"]').hide();
    }, 5);
    frappe.call({
        method:'masar_miraaya.custom.sales_order.sales_order.delivery_warehouse',
        callback:function(r){
            if (r.message){
                console.log(r.message);
                frm.doc.parent_warehouse = r.message;
                frm.refresh_field("parent_warehouse");
            }
        }
        })
}
function create_picked_button(frm) {
    if(frm.doc.docstatus === 1 && frm.doc.custom_packed === 0 ) { 
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
    if(frm.doc.docstatus === 1 && frm.doc.status !=='Completed' && frm.doc.custom_packed === 1 ) { 
        frm.add_custom_button(__('Transfer'), function() {
            frappe
			.xcall("masar_miraaya.custom.pick_list.pick_list.stock_entry_method", {
				self: frm.doc,
			})
			.then((stock_entry) => {
                frm.reload_doc();
                console.log(stock_entry.name);
				frappe.set_route("Form", "Stock Entry", stock_entry.name);
			});
        });
    }
}