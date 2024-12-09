import frappe
from masar_miraaya.api import update_stock_magento_stock_entry
from masar_miraaya.api import update_stock_magento_pr


def on_submit(self, method):
    if self.docstatus == 1 and self.stock_entry_type == 'Material Issue':
        update_stock_magento_stock_entry(self)

def on_cancel(self, method):
    if self.stock_entry_type == 'Material Issue':
        update_stock_magento_pr(self)
    pass