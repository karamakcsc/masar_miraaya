import frappe
import requests
from masar_miraaya.api import base_data


def on_submit(self, method):
    # if self.docstatus == 1:
    #     update_stock_magento(self)
    pass

def get_warehouse_code_magento():
    base_url, headers = base_data("magento")
    url = base_url + "/rest/V1/inventory/sources"
    
    response = requests.get(url, headers=headers)
    json_response = response.json()
    if response.status_code == 200:
        return json_response
    else:
        frappe.throw(f"Error in Getting Warehouse Code. {str(response.text)}")


def get_magento_item_stock(item_code):
    base_url, headers = base_data("magento")
    url = base_url + f"/rest/V1/stockItems/{item_code}"
    response = requests.get(url, headers=headers)
    json_response = response.json()
    if response.status_code == 200:
        return json_response
    else:
        frappe.throw(f"Error in Getting Item Stock. {str(response.text)}")


def update_stock_magento(self):
    base_url, headers = base_data("magento")
    url = base_url + "/rest/V1/inventory/source-items"
    
    warehouse_codes = get_warehouse_code_magento() ## GET Warehouse Codes (source_code) from Magento
    
    item_list = []
    for row in self.items:
        sku = row.item_code
        qty = row.qty
        warehouse = row.warehouse
        
        item_stock = get_magento_item_stock(sku) ## GET Item Stock
        stock_qty = item_stock.get('qty')
        stock = stock_qty + qty  ## Add Existing qty with new qty
        
        item_list.append({
            "sku": sku,
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