import frappe
from masar_miraaya.api import update_stock_magento_pr


def on_submit(self, method):
    update_stock(self)


def update_stock(self):
    if self.docstatus == 1:
        update_stock_magento_pr(self)
