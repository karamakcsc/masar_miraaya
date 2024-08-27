import frappe
import json
import requests
from masar_miraaya.api import base_request_magento_data

def after_save(self, method):
    if self.custom_is_publish and self.custom_is_publish is not None:
        create_new_item_group(self)
    pass


def get_magento_categories():
    base_url, headers = base_request_magento_data()
    url = f"{base_url}/rest/all/V1/categories"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        category_names = []
        
        def extract_names(category):
            if 'name' in category:
                category_names.append(category['name'])
            if 'children_data' in category:
                for child in category['children_data']:
                    extract_names(child)
        
        extract_names(data)
        
        return category_names
    except requests.RequestException as e:
        frappe.throw(f"Error fetching Magento categories: {str(e)}")
        return []


def create_new_item_group(self):
    base_url, headers = base_request_magento_data()
    # if self.is_new() == 1:

    is_active = 0

    if self.custom_is_publish == 1:
            is_active = 1
    else:
        is_active = 0

    if self.name not in get_magento_categories():
        parent_id = 1 if self.is_group == 1 else self.custom_parent_item_group_id
        
        if self.custom_is_publish == 1:
            is_active = True
        else:
            is_active = False
        data = {
            "category": {
                "parent_id": parent_id,
                "name": self.item_group_name,
                "is_active": is_active,
                "position": 1,
                "include_in_menu": True
            }
        }
        
        url = base_url + "/rest/V1/categories"
        
        try:
            response = requests.post(url, headers=headers, json=data)
            json_response = response.json()
            group_id = json_response['id']
            self.custom_item_group_id = group_id
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            frappe.throw(f"Failed to create item group in Magento: {str(e)}")
    else:

        if self.custom_is_publish == 1:
            is_active = True
        else:
            is_active = False

        parent_id = self.custom_parent_item_group_id

        data = {
                "parent_id": parent_id,
                "is_active": is_active,
        }
        url = base_url + f"/rest/V1/categories/{self.custom_item_group_id}/move"
        try:
            response = requests.put(url, headers=headers, json=data)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            frappe.throw(f"Failed to update item group in Magento: {str(e)}")
            
@frappe.whitelist()
def get_parent_item_group_id(parent_id):
    query = frappe.db.sql(f"""
                         SELECT custom_item_group_id FROM `tabItem Group` WHERE name = '{parent_id}'
                         """, as_dict=True)
    parent_group_id = query[0]['custom_item_group_id']
    return parent_group_id
