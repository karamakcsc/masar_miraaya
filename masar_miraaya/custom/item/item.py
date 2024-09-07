import frappe
import requests
import json
import base64
import os
from masar_miraaya.api import base_request_magento_data

        
def validate(self, method):
    if self.custom_is_publish and self.custom_created_in_frappe:
        create_new_item(self)
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
    try:
        base_url, headers = base_request_magento_data()
        url = f"{base_url}/rest/V1/products/{self.item_code}"

        is_active = 1 if self.disabled == 0 else 0
        
        visibility = {
            'Not Visible Individually': 1,
            'Catalog': 2,
            'Search': 3,
            'Catalog & Search': 4
        }.get(self.custom_visibility, 1)

        if not self.get('barcodes'):
            frappe.throw("Please Add Barcode")

        ean = None
        for barcode in self.get('barcodes'):
            if barcode.barcode_type == 'EAN':
                ean = barcode.barcode
                str_ean = str(ean)
        
        attribute = ''
        attribute_list = []
        for attribute in self.get('attributes'):
            if self.variant_based_on == 'Item Attribute':
                attribute = attribute.attribute
                attribute_list.append(attribute)
        
        frappe.throw(str(attribute_list))
        
        product_type = "configurable" if self.has_variants else self.custom_magento_item_type.lower()
        
        data = {
            "product": {
                "sku": self.item_code,
                "name": self.item_name,
                "price": 200,
                "status": is_active,
                "visibility": visibility,
                "type_id": product_type,
                "attribute_set_id": 16,
                "extension_attributes": {
                    "website_ids": [
                        1
                    ],
                "category_links": [
                    {
                    "position": 0,
                    "category_id": self.custom_root_item_group_id if self.custom_root_item_group_id else 0
                    },
                    {
                    "position": 1,
                    "category_id": self.custom_parent_item_group_id if self.custom_parent_item_group_id else 0
                    },
                    {
                    "position": 2,
                    "category_id": self.custom_item_group_id if self.custom_item_group_id else 0
                    }
                ]
                },
                "custom_attributes": [
                        {
                            "attribute_code": "brand",
                            "value": self.brand
                        },
                        {
                            "attribute_code": "free_from",
                            "value": self.custom_free_from
                        },
                        {
                            "attribute_code": "key_features",
                            "value": self.custom_key_features
                        },
                        {
                            "attribute_code": "options_container",
                            "value": "container2"
                        },
                        {
                            "attribute_code": "url_key",
                            "value": self.name + self.item_name
                        },
                        {
                            "attribute_code": "ingredients",
                            "value": self.custom_ingredients
                        },
                        {
                            "attribute_code": "ean",
                            "value": str_ean
                        },
                        {
                            "attribute_code": "tax_class_id",
                            "value": 2 if self.custom_is_taxable else 0
                        },
                        {
                            "attribute_code": "how_to_use",
                            "value": self.custom_how_to_use
                        },
                        {
                            "attribute_code": "arabic_name",
                            "value": self.custom_item_name_ar
                        },
                        {
                            "attribute_code": "formulation",
                            "value": self.custom_formulation
                        },
                        {
                            "attribute_code": "product_description",
                            "value": self.description
                        },
                        {
                            "attribute_code": "country_of_manufacture",
                            "value": self.custom_country_of_manufacture
                        },
                        {
                            "attribute_code": "size_ml",
                            "value": self.custom_size_ml if self.custom_size_ml else 0
                        },
                        {
                            "attribute_code": "size",
                            "value": self.custom_size if self.custom_size else 0
                        },
                        {
                            "attribute_code": "shade",
                            "value": self.custom_shade if self.custom_shade else 0
                        },
                        {
                            "attribute_code": "color",
                            "value": self.custom_color if self.custom_color else 0
                        }
                    ]
                },
            "saveOptions": True
            }
        attribute_id = {
            "Color": 93,
            "Shade": 159,
            "Size": 144,
            "Size (ml)": 158
        }

        configurable_product_options = []

        if product_type == "configurable":
            for label in attribute_list:
                configurable_product_options.append({
                    "attribute_id": attribute_id.get(label, ""),
                    "label": label,
                    "values": [
                        {"value_index": 239},
                        {"value_index": 244},
                        {"value_index": 245},
                        {"value_index": 246}
                    ],
                })

            data["product"]["extension_attributes"]["configurable_product_options"] = configurable_product_options
            data["product"]["extension_attributes"]["configurable_product_links"] = [
                2139,
                2140,
                2141,
                2142
            ]
        
        # response = requests.put(url, headers=headers, json=data)
        # if response.status_code == 200:
        #     json_response = response.json()
        #     item_id = json_response['id']
        #     self.custom_item_id = item_id
        #     frappe.msgprint(f"Item Created/Updated Successfully in Magento: {str(response.text)}")
            
        # else:
        #     frappe.throw(f"Failed to Create or Update Item in Magento: {str(response.text)}")
  
    except requests.RequestException as e:
        frappe.throw(f"Failed to Create or Update Item in Magento: {str(e)}")



@frappe.whitelist()
def add_image_to_item(self, file_path):
    try:
        image_path = file_path
        if not image_path:
            frappe.throw("Image path is empty. Please ensure the image is attached to the Item.")
        if "files/" in image_path:
            image = image_path.split("files/")[1]
        else:
            frappe.throw("Invalid image path format. 'files/' not found in the path.")
        
        bench_path = frappe.utils.get_bench_path()
        site_name = frappe.utils.get_site_name(frappe.local.site)
        file_path = os.path.join(bench_path, 'sites', site_name, 'public', 'files', image)

        if not os.path.exists(file_path):
            frappe.throw(f"File not found at {file_path}")
        
        with open(file_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

        base_url, headers = base_request_magento_data()
        data = {
            "entry": {
                "media_type": "image",
                "label": "",
                "position": 1,
                "disabled": False,
                "types": [
                    "image",
                    "small_image",
                    "thumbnail",
                    "swatch_image"
                ],
                "content": {
                    "base64_encoded_data": encoded_image,
                    "type": "image/jpeg",
                    "name": image
                }
            }
        }
        url = base_url + f"/rest/V1/products/{self.item_code}/media"
    
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            frappe.msgprint("Image Added to Item Successfully")
        else:
            frappe.throw(f"Error Image: {response.text}")
    
    except Exception as e:
        frappe.throw(f"Failed to add image to product in Magento: {str(e)}")

@frappe.whitelist()
def get_magento_image_id(self, image_path):
    try:
        base_url, headers = base_request_magento_data()
        
        url = base_url + f"/rest/default/V1/products/{self.item_code}/media"
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            image_data = response.json()
        else:
            frappe.throw(f"Error Deleting Image: {response.text}")
        
        # filename = image_path.split('/')[-1]
        # frappe.throw(str(filename))
        for data in image_data:
            magento_filename = data['file'].split('/')[-1]
            if magento_filename == image_path:
                entity_id = data['id']
        # frappe.msgprint(str(magento_filename))        
        if entity_id:
            remove_image_from_magento(self, entity_id)    
            
            
    except Exception as e:
        return f"Error GET Magento image ID: {e}"

@frappe.whitelist()
def remove_image_from_magento(self, entity_id):
    base_url, headers = base_request_magento_data()
    try:
        url = base_url + f"/rest/V1/products/{self.item_code}/media/{entity_id}"
        
        response = requests.delete(url, headers=headers)
        
        if response.status_code == 200:
            frappe.msgprint("Image Deleted Successfully From Magento")
        else:
            frappe.throw(f"Error Deleting Image: {response.text}")
            
    except Exception as e:
        frappe.throw(str(f"Error Removing Image from Magento: {e}"))
    

        
# @frappe.whitelist()
# def get_item_group_id(item_group):
#     query = frappe.db.sql(f"""
#                          SELECT custom_item_group_id FROM `tabItem Group` WHERE name = '{item_group}'
#                          """, as_dict=True)
#     parent_group_id = query[0]['custom_item_group_id']
#     return parent_group_id