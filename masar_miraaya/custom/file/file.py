import frappe
import requests
import base64
import os
from masar_miraaya.custom.item.item import  base_data , remove_image_from_magento
def validate(self, method):
    if self.attached_to_doctype == 'Item' and self.custom_magento_sync == 0 :
        doc = frappe.get_doc('Item', self.attached_to_name)
        file_path = self.file_url
        add_image_to_item(doc, file_path)

def on_trash(self, method):
    if self.attached_to_doctype == 'Item':
        doc = frappe.get_doc('Item', self.attached_to_name)
        get_magento_image_id(doc, self.file_name)
        

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

        base_url, headers = base_data("magento")
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
        base_url, headers = base_data("magento")
        
        url = base_url + f"/rest/default/V1/products/{self.item_code}/media"
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            image_data = response.json()
        else:
            frappe.throw(f"Error Deleting Image: {response.text}")
        

        for data in image_data:
            magento_filename = data['file'].split('/')[-1]
            if magento_filename == image_path:
                entity_id = data['id']
        if entity_id:
            remove_image_from_magento(self, entity_id)    
            
            
    except Exception as e:
        return f"Error GET Magento image ID: {e}"