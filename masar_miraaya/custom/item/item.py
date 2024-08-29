import frappe
import requests
import json
import base64
import os
from masar_miraaya.api import base_request_magento_data

def on_change(self , method):
    # if self.is_new() == 0:
    # if self.image and self.image is not None:
    #     add_image_to_item(self)
    pass
        
def after_save(self, method):
    # if self.custom_is_publish:
    # create_new_item(self)
    pass
    
@frappe.whitelist()
def get_values(item_code):
    warehouse = frappe.db.get_value(
        'Item Default',
        {'parent': item_code},
        'default_warehouse'
    )
    item_actual_qty = frappe.db.sql("""
        SELECT actual_qty 
        FROM `tabBin` 
        WHERE item_code = %s AND warehouse = %s
    """, (item_code, warehouse), as_dict=True)
    
    if item_actual_qty:
        actual_qty = item_actual_qty[0].get('actual_qty', 0)
    else:
        actual_qty = 0

    return actual_qty


@frappe.whitelist()
def create_new_item(self):
    base_url, headers = base_request_magento_data()
    url = f"{base_url}/rest/V1/products"

    is_active = 0

    if self.disabled == 0 and self.custom_is_publish == 1:
        is_active = 1
    else:
        is_active = 0

    # elif self.custom_is_publish == 1:
    #     is_active = 1
    # else:
    #     is_active = 0
    data = {
        "product": {
            "sku": self.item_code,
            "name": self.item_name,
            "price": 100,
            "status": is_active,
            "type_id": "simple",
            "attribute_set_id": 4,
            "extension_attributes": {
                "stock_item": {
                    "qty": 100,
                    "is_in_stock": True
                },
                "category_links": [
                    {
                        "position": 0,
                        "category_id": self.custom_item_group_id
                    }
                ]
            },
            "custom_attributes": [
                {
                    "attribute_code": "description",
                    "value": self.description
                }
            ]
        },
        "saveOptions": True
    }

    get_sku_url = f"{base_url}/rest/V1/products?fields=items[sku]&searchCriteria[pageSize]=1000"


    try:
        sku_response = requests.get(get_sku_url, headers=headers)
        sku_response.raise_for_status()

        existing_skus = [item['sku'] for item in sku_response.json().get('items', [])]

        if self.item_code in existing_skus:
            update_item_if_exists(self, base_url, headers)
        else:
            # if self.is_new() == 1:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            # else:
            #     update_item_if_exists(self, base_url, headers)
                
    except requests.exceptions.RequestException as e:
        frappe.throw(f"Failed to sync item with Magento: {str(e)}")


def update_item_if_exists(self, base_url, headers):
    search_url = f"{base_url}/rest/V1/products/{self.item_code}"

    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        item = response.json()

        is_active = 1

        if self.disabled == 0 and self.custom_is_publish == 0:
            is_active = 0
        elif self.disabled == 1 and self.custom_is_publish == 0:
            is_active = 0
        elif self.disabled == 1 and self.custom_is_publish == 1:
            is_active = 0
        elif self.disabled == 0 and self.custom_is_publish == 1:
            is_active = 1
        else:
            is_active = 0

        if item:
            update_url = f"{base_url}/rest/V1/products/{self.item_code}"
            update_data = {
                "product": {
                    "sku": self.item_code,
                    "name": self.item_name,
                    "price": 100,
                    "status": is_active,
                    "type_id": "simple",
                    "attribute_set_id": 4,
                    "extension_attributes": {
                        "stock_item": {
                            "qty": 100,
                            "is_in_stock": True
                        },
                        "category_links": [
                            {
                                "position": 0,
                                "category_id": self.custom_item_group_id
                            }
                        ]
                    },
                    "custom_attributes": [
                        {
                            "attribute_code": "description",
                            "value": self.description
                        }
                    ]
                }
            }
            update_response = requests.put(update_url, headers=headers, json=update_data)
            update_response.raise_for_status()
            
    except requests.exceptions.RequestException as e:
        frappe.throw(f"Failed to update item: {str(e)}")

@frappe.whitelist()
def add_image_to_item(self):
    image_path = self.image
    image = image_path.split("files/")[1]
    bench_path = frappe.utils.get_bench_path()
    site_name = frappe.utils.get_site_name(frappe.local.site)
    file_path = os.path.join(bench_path, 'sites', site_name, 'public', 'files', image)
    with open(file_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
    base_url, headers = base_request_magento_data()
    data = {
        "entry": {
            "media_type": "image",
            "label": "Image",
            "position": 1,
            "disabled": False,
            "types": [
                "image",
                "small_image",
                "thumbnail"
            ],
            "content": {
                "base64_encoded_data": encoded_image,
                "type": "image/jpeg",
                "name": "makeup_img.jpg"
            }
        }
    }
    url = base_url + f"/rest/V1/products/{self.item_code}/media"
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        frappe.throw(f"Failed to create item in Magento: {str(e)}")
        
        
@frappe.whitelist()
def get_item_group_id(item_group):
    query = frappe.db.sql(f"""
                         SELECT custom_item_group_id FROM `tabItem Group` WHERE name = '{item_group}'
                         """, as_dict=True)
    parent_group_id = query[0]['custom_item_group_id']
    return parent_group_id