import frappe
import json
import requests
from masar_miraaya.api import base_data



def validate(self , method):
    check_new_brand(self)
    
    
def check_new_brand(self):
    if self.custom_publish_to_magento:
        magento = frappe.get_doc('Magento Sync')
        if magento.sync == 0 :
            create_new_brand(self.brand)
        else: 
            frappe.throw("Set Sync in Magento Sync disabled. To Update/Create in magento.")
        

@frappe.whitelist()    
def create_new_brand(brand):
    try:
        base_url, headers = base_data("magento")
        url = base_url + "/rest/V1/products/attributes/163"
        
        data = {
            "attribute": {
                "attribute_id": 163,
                "attribute_code": "brand",
                "frontend_input": "text",
                "entity_type_id": "4",
                "is_required": False,
                "options": [
                    {
                        "label": brand,
                        "value": brand
                    }
                ]
            }
        }
            
        response = requests.put(url, headers=headers, json=data)
        if response.status_code == 200:
            frappe.msgprint("Brand Created Successfully in Magento")
        else:
            frappe.throw(f"Failed to Create Brand in Magento: {str(response.text)}")
                
    except Exception as e:
        frappe.throw(f"Failed to create Brand: {str(e)}")