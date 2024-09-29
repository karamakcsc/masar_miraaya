import frappe
import json
import requests
from masar_miraaya.api import base_data

def validate(self , method):
    roles = (frappe.get_roles(frappe.session.user))
    if (self.custom_publish_to_magento and ('API Integration' not in roles)) or (self.custom_publish_to_magento and frappe.session.user == 'Administrator' ):
        magento = frappe.get_doc('Magento Sync')
        if magento.sync == 0 : 
            update_magento_price(self)
        else: 
            frappe.throw("Set Sync in Magento Sync disabled. To Update/Create in magento.")

        
@frappe.whitelist()    
def update_magento_price(self):
    # try:
        item_doc = frappe.get_doc("Item", self.item_code)
        if not item_doc.custom_is_publish:
            frappe.throw("The Item Must be Publish to Magento")
            
        if self.price_list:
            price_list_doc=frappe.get_doc('Price List',self.price_list)
            if not price_list_doc.custom_magento_selling:
                frappe.throw("Failed to Update Product Price in Magento Because The Price List Used Isn't the Magento Default ")
        
        base_url, headers = base_data("magento")
        url = base_url + "/rest/V1/products/base-prices"
        
        data = {
            "prices": [
                {
                "price": self.price_list_rate,
                "store_id": 1,
                "sku": self.item_code
                }
            ]
        }
            
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            frappe.msgprint("Product Price Updated Successfully in Magento", alert=True , indicator='green')
        else:
            frappe.throw(f"Failed to Update Product Price in Magento: {str(response.text)}")
                
    # except Exception as e:
    #     frappe.throw(f"Failed to Update Item Price: {str(e)}")

