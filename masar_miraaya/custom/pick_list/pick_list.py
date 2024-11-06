import frappe
from erpnext.stock.doctype.pick_list.pick_list import create_stock_entry


@frappe.whitelist()
def new_stock_entry(pick_list):
    dict_ = create_stock_entry(pick_list)
    if dict_ is not None:
        frappe.new_doc('Stock Entry').update(dict_).save().submit()