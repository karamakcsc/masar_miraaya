frappe.ui.form.on('Item Alternative', {
    refresh: function(frm) {
        frm.toggle_display("two_way", false);
    },
    onload: function(frm){
        frm.toggle_display("two_way", false);
    },
    setup: function(frm){
        frm.toggle_display("two_way", false);
    }
  });