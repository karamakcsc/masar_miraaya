import frappe
import requests
from masar_miraaya.api import base_data


def validate(self, method):
    if self.custom_is_publish:
        base_url, headers = base_data("magento")
        data = {
            "product": {
                "sku": self.item_code,
                "name": self.item_name,
            }
        }
        url = f"{base_url}/rest/V1/products/{self.item_code}"
        
        product_link = [{
            "sku": self.item_code,
            "link_type": "related",
            "linked_product_sku": self.alternative_item_code,
            "linked_product_type": "simple",
            "position": 0,
        }]
            
        if product_link:    
            data["product"]["product_links"] = product_link

        response = requests.put(url, headers=headers, json=data)
        if response.status_code == 200:
            frappe.msgprint(f"Item Alternative Created Successfully in Magento" , alert=True , indicator='green')
            
        else:
            frappe.throw(f"Failed to Create or Update Item Alternative in Magento: {str(response.text)}")