import frappe
import requests
from masar_miraaya.api import base_data, get_qty_items_details, get_magento_item_stock , request_with_history


def on_submit(self, method):
    if self.stock_entry_type == 'Material Issue':
        update_stock(self , '-')
    if self.stock_entry_type == 'Material Transfer':
        update_stock_transfer(self, '-')

def on_cancel(self, method):
    if self.stock_entry_type == 'Material Issue':
        update_stock(self , '+')
    if self.stock_entry_type == 'Material Transfer':
        update_stock_transfer(self, '+')
    
    
    
def update_stock(self , operation):
        base_url, headers = base_data("magento")
        url = base_url + "/rest/V1/inventory/source-items"
        item_list = []
        sql = get_qty_items_details(self.doctype, 'Stock Entry Detail', self.name)
        
        if sql:
            for item in sql:
                item_doc = frappe.get_doc("Item", item.item_code)
                if item_doc.custom_is_publish == 0:
                    continue
                item_stock = get_magento_item_stock(item.item_code)
                stock_qty = item_stock.get('qty') if item_stock.get('qty') else 0
                
                if operation == '+': 
                    stock = stock_qty + item.qty
                elif operation == '-': 
                    if stock_qty < item.qty:
                        frappe.throw(f"The Qty: {item.qty}, is More than the Stock Qty in Magento: {stock_qty}")
                    stock = stock_qty - item.qty
                item_list.append({
                    "sku": item.item_code,
                    "source_code": "default",
                    "quantity": stock,
                    "status": 1 ## if 1 in stock , 0 out of stock
                })
            
            if item_list:    
                payload = {
                    "sourceItems": item_list
                }
                
                response = request_with_history(
                        req_method='POST', 
                        document=self.doctype, 
                        doctype=self.name, 
                        url=url, 
                        headers=headers  ,
                        payload=payload        
                    )
                if response.status_code == 200:
                    frappe.msgprint("Item Stock Updated Successfully in Magento", alert=True , indicator='green')
                else:
                    frappe.throw(f"Failed to Update Item Stock in Magento: {str(response.text)}")

def update_stock_transfer(self , operation):
        base_url, headers = base_data("magento")
        url = base_url + "/rest/V1/inventory/source-items"
        item_list = []
        sql = get_qty_items_details(self.doctype, 'Stock Entry Detail', self.name)
        warehouse_sql = frappe.db.sql("""
                                      SELECT tw.name FROM tabWarehouse tw WHERE tw.name NOT LIKE 'C%'
                                      """, as_dict=True)
        
        warehouse = [a.name for a in warehouse_sql if a.name]
        # frappe.throw(str(warehouse)) 
        if sql:
            for item in sql:
                item_doc = frappe.get_doc("Item", item.item_code)
                if item_doc.custom_is_publish == 0:
                    continue
                if item.s_warehouse not in [warehouse]:
                    item_stock = get_magento_item_stock(item.item_code)
                    stock_qty = item_stock.get('qty') if item_stock.get('qty') else 0
                    
                    if operation == '+': 
                        stock = stock_qty + item.qty
                    elif operation == '-': 
                        if stock_qty < item.qty:
                            frappe.throw(f"The Qty: {item.qty}, is More than the Stock Qty in Magento: {stock_qty}")
                        stock = stock_qty - item.qty
                    item_list.append({
                        "sku": item.item_code,
                        "source_code": "default",
                        "quantity": stock,
                        "status": 1 ## if 1 in stock , 0 out of stock
                    })
                
                if item_list:    
                    payload = {
                        "sourceItems": item_list
                    }
                    
                    # frappe.throw(str(payload))
                    
                    response = request_with_history(
                            req_method='POST', 
                            document=self.doctype, 
                            doctype=self.name, 
                            url=url, 
                            headers=headers  ,
                            payload=payload        
                        )
                    if response.status_code == 200:
                        frappe.msgprint("Item Stock Updated Successfully in Magento", alert=True , indicator='green')
                    else:
                        frappe.throw(f"Failed to Update Item Stock in Magento: {str(response.text)}")