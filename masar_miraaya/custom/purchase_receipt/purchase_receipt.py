import frappe
from masar_miraaya.api import update_stock_magento_pr
from masar_miraaya.api import update_stock_magento_stock_entry


def on_submit(self, method):
    update_stock(self)

def on_cancel(self, method):
    update_stock_magento_stock_entry(self)
    pass
    
    
def update_stock(self):
    if self.docstatus == 1:
        update_stock_magento_pr(self)
