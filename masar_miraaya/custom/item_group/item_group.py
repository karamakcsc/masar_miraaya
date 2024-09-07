import frappe
import json
import requests
from masar_miraaya.api import base_request_magento_data

def validate(self, method):
    if self.custom_is_publish and self.custom_created_in_frappe:
        create_new_item_group(self)
    pass


def create_new_item_group(self):
    try:
        base_url, headers = base_request_magento_data()

        is_active = 1 if self.custom_is_publish else 0
            
        data = {
            "category": {
                "parent_id": self.custom_parent_item_group_id,
                "name": self.name.split(' - ', 1)[-1].strip(),
                "is_active": is_active,
                "position": 1,
                "include_in_menu": True
            }
        }
        # if self.is_group == 1:
        #     data["category"]["children_data"] = []
        
        url = base_url + "/rest/V1/categories"
        if self.is_new() == 1:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                json_response = response.json()
                group_id = json_response['id']
                self.custom_item_group_id = group_id
                frappe.msgprint("Category Created Successfully in Magento")
            else:
                frappe.throw(f"Failed To Create Category in Magento: {str(response.text)}")
        else:
            url = base_url + f"/rest/V1/categories/{self.custom_item_group_id}/move"
            
            data = {
                "parentId": self.custom_parent_item_group_id
            }
            
            response = requests.put(url, headers=headers, json=data)
            
            if response.status_code == 200:
                frappe.msgprint("Category Updated Successfully in Magento")
            else:
                frappe.throw(f"Failed to Update Category in Magento: {str(response.text)}")
                
    except requests.exceptions.RequestException as e:
        frappe.throw(f"Failed to create item group in Magento: {str(e)}")


            
@frappe.whitelist()
def get_parent_item_group_id(parent_id):
    query = frappe.db.sql(f"""
                         SELECT custom_item_group_id FROM `tabItem Group` WHERE name = '{parent_id}'
                         """, as_dict=True)
    parent_group_id = query[0]['custom_item_group_id']
    return parent_group_id
