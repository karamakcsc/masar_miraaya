import frappe
import requests
from masar_miraaya.api import base_data, get_qty_items_details, get_magento_item_stock


def on_submit(self, method):
    update_stock(self , '+')

def on_cancel(self, method):
    update_stock(self , '-')
    
    
    
def update_stock(self , operation):
        base_url, headers = base_data("magento")
        url = base_url + "/rest/V1/inventory/source-items"
        item_list = []
        sql = get_qty_items_details(self.doctype, 'Purchase Receipt Item', self.name)
        # frappe.throw(f"Item: {sql}")
        
        if sql:
            for item in sql:
                item_stock = get_magento_item_stock(item.item_code)
                stock_qty = item_stock.get('qty') if item_stock.get('qty') else 0
                if operation == '+': 
                    stock = stock_qty + item.qty
                elif operation == '-': 
                    stock = stock_qty - item.qty
                item_list.append({
                    "sku": item.item_code,
                    "source_code": "default",
                    "quantity": stock,
                    "status": 1 ## if 1 in stock , 0 out of stock
                })
                
            payload = {
                "sourceItems": item_list
            }
            
            # frappe.throw(str(payload))
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                frappe.msgprint("Item Stock Updated Successfully in Magento", alert=True , indicator='green')
            else:
                frappe.throw(f"Failed to Update Item Stock in Magento: {str(response.text)}")
