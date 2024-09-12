import frappe
import json
import requests
from masar_miraaya.api import base_data

def validate(self, method):
    if self.custom_is_publish:
        magento = frappe.get_doc('Magento Sync')
        if magento.sync == 0 :  
            create_new_item_group(self)
        else: 
            frappe.throw("Set Sync in Magento Sync disabled. To Update/Create in magento.")
            
def create_new_item_group(item_group_name):
    doc = frappe.get_doc('Item Group', item_group_name)
    try:
        base_url, headers = base_data("magento")

        is_active = 1 if doc.custom_is_publish else 0
            
        data = {
            "category": {
                "parent_id": doc.custom_parent_item_group_id,
                "name": doc.name.split(' - ', 1)[-1].strip(),
                "is_active": is_active,
                "position": 1,
                "include_in_menu": True
            }
        }
        
        url = base_url + "/rest/V1/categories"
        if doc.is_new() == 1:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                json_response = response.json()
                group_id = json_response['id']
                doc.custom_item_group_id = group_id
                frappe.msgprint("Category Created Successfully in Magento")
            else:
                frappe.throw(f"Failed To Create Category in Magento: {str(response.text)}")
        else:
            url = base_url + f"/rest/V1/categories/{doc.custom_item_group_id}/move"
            
            data = {
                "parentId": doc.custom_parent_item_group_id
            }
            
            response = requests.put(url, headers=headers, json=data)
            
            if response.status_code == 200:
                frappe.msgprint("Category Updated Successfully in Magento")
            else:
                frappe.throw(f"Failed to Update Category in Magento: {str(response.text)}")
                
    except requests.exceptions.RequestException as e:
        frappe.throw(f"Failed to create item group in Magento: {str(e)}")
