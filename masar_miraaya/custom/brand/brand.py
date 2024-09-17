import frappe
import json
import requests
from masar_miraaya.api import base_data



def validate(self , method):
    if self.custom_publish_to_magento:
        magento = frappe.get_doc('Magento Sync')
        if magento.sync == 0 :
            create_new_brand(self)
        else: 
            frappe.throw("Set Sync in Magento Sync disabled. To Update/Create in magento.")
        

@frappe.whitelist()    
def create_new_brand(self):
    try:
        new_item_group = frappe.new_doc("Item Group")
        new_item_group.item_group_name = self.name
        new_item_group.parent_item_group = '404 - Brands'
        new_item_group.save(ignore_permissions = True)
        
        base_url, headers = base_data("magento")
        url = base_url + f"/rest/V1/categories/0"        
        
        data = {
            "category": {
                "parent_id": 404,
                "name": self.name.split(' - ', 1)[-1].strip(),
                "is_active": True,
                "position": 1,
                "include_in_menu": True
            }
        }
            
        response = requests.put(url, headers=headers, json=data)
        if response.status_code == 200:
            json_response = response.json()
            group_id = json_response['id']
            new_item_group.custom_item_group_id = group_id
            new_item_group.save(ignore_permissions = True)
            frappe.db.set_value("Item Group" ,new_item_group.name , 'custom_is_publish' , 1 )
            frappe.db.commit()
            frappe.msgprint("Brand Created Successfully in Magento", alert = True, indicator = 'green')
        else:
            frappe.throw(f"Failed to Create Brand in Magento: {str(response.text)}")
                
    except Exception as e:
        frappe.throw(f"Failed to create Brand: {str(e)}")