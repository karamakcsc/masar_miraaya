import frappe
import json
import requests
from masar_miraaya.api import base_data

def validate(self , method):
    if self.custom_publish_to_magento:
        magento = frappe.get_doc('Magento Sync')
        if magento.sync == 0 : 
            update_magento_price(self.item_code, self.price_list_rate)
        else: 
            frappe.throw("Set Sync in Magento Sync disabled. To Update/Create in magento.")
        
@frappe.whitelist()    
def update_magento_price(item_code, price_list_rate):
    try:
        base_url, headers = base_data("magento")
        url = base_url + "/rest/V1/products/base-prices"
        
        data = {
            "prices": [
                {
                "price": price_list_rate,
                "store_id": 1,
                "sku": item_code
                }
            ]
        }
            
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            frappe.msgprint("Product Price Updated Successfully in Magento")
        else:
            frappe.throw(f"Failed to Update Product Price in Magento: {str(response.text)}")
                
    except Exception as e:
        frappe.throw(f"Failed to Update Item Price: {str(e)}")