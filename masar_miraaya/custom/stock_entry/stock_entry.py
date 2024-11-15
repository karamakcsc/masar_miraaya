import frappe
from masar_miraaya.api import update_stock_magento_stock_entry


def on_submit(self, method):
    if self.docstatus == 1 and self.stock_entry_type == 'Material Issue':
        update_stock_magento_stock_entry(self)
