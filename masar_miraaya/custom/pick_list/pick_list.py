import frappe
from erpnext.stock.doctype.pick_list.pick_list import create_stock_entry
import json

@frappe.whitelist()
def new_stock_entry(pick_list):
    dict_ = json.dumps(create_stock_entry(pick_list))
    if bool(dict_) == True and str(dict_) != 'null':
        #
        frappe.new_doc('Stock Entry').update(json.loads(dict_)).save().submit()