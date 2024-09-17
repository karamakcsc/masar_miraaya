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
            
def after_rename(self, method, old, new, merge):
    if self.custom_is_publish:
        magento = frappe.get_doc('Magento Sync')
        if magento.sync == 0 :
            update_item_group_name(self)
        else: 
            frappe.throw("Set Sync in Magento Sync disabled. To Update/Create in magento.")            

            
def create_new_item_group(self):
    try:
        base_url, headers = base_data("magento")

        is_active = self.custom_disabled
        # frappe.throw(str(is_active))
        brand_sql = frappe.db.sql(" SELECT name FROM tabBrand WHERE name = %s", (self.name.split(' - ', 1)[-1].strip()), as_dict=True)
        if int(self.custom_parent_item_group_id) == 404 or ( brand_sql and brand_sql[0] and brand_sql [0]['name']):
                frappe.throw("Cannot Change Parent Item Group")
        elif int(self.custom_parent_item_group_id) == 404:
                frappe.throw("To Create Brand, Create it in Doc 'Brand'.")
            
        
            
        data = {
            "category": {
                "parent_id": self.custom_parent_item_group_id,
                "name": self.name.split(' - ', 1)[-1].strip(),
                "is_active": bool(is_active),
                "position": 1,
                "include_in_menu": True
            }
        }
        if self.custom_item_group_id:
            item_group_id = self.custom_item_group_id
        else:
            item_group_id = 0
            
        url = base_url + f"/rest/V1/categories/{item_group_id}"
        response = requests.put(url, headers=headers, json=data)
        if response.status_code == 200:
            json_response = response.json()
            group_id = json_response['id']
            self.custom_item_group_id = group_id
            if json_response['parent_id'] != self.custom_parent_item_group_id:
                url = base_url + f"/rest/V1/categories/{group_id}/move"
                data = {
                    "parentId": self.custom_parent_item_group_id,
                }
                response = requests.put(url, headers=headers, json=data)
            frappe.msgprint("Category Created/Updated Successfully in Magento", alert = True, indicator = 'green')
        else:
                frappe.throw(f"Failed To Created/Updated Category in Magento: {str(response.text)}")
    except requests.exceptions.RequestException as e:
        frappe.throw(f"Failed to create item group in Magento: {str(e)}")


def update_item_group_name(self):
    try:
        base_url, headers = base_data("magento")
        url = base_url + f"/rest/V1/categories/{self.custom_item_group_id}"
        is_active = True if not self.custom_disabled else False
        data = {
            "category": {
                 "id": self.custom_item_group_id,
                "parent_id": self.custom_parent_item_group_id,
                "name": self.name.split(' - ', 1)[-1].strip(),
                "is_active": is_active,
                "position": 1,
                "include_in_menu": True
            }
        }
        response = requests.put(url, headers=headers, json=data)
        if response.status_code == 200:
            json_response = response.json()
            group_id = json_response['id']
            self.custom_item_group_id = group_id
            frappe.msgprint(f"Item Group Updated Successfully in Magento" , alert=True , indicator='green')
        else:
            frappe.throw(f"Failed To Updated Item Group in Magento: {str(response.text)}")
    except Exception as e:
        frappe.throw(f"Failed to rename Item Group: {str(e)}")