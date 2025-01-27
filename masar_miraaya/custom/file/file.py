import frappe
import requests
import base64
import os
from masar_miraaya.api import base_data , request_with_history
def validate(self, method):
    if self.attached_to_doctype == 'Item' and self.custom_magento_sync == 0 :
        doc = frappe.get_doc('Item', self.attached_to_name)
        if doc.custom_is_publish ==1:
            file_path = self.file_url
            add_image_to_item(self, doc, file_path)

def on_trash(self, method):
    if self.attached_to_doctype == 'Item' and self.custom_magento_sync == 0:
        doc = frappe.get_doc('Item', self.attached_to_name)
        if doc.custom_is_publish ==1:
            get_magento_image_id(doc, self.file_name)
        

@frappe.whitelist()
def add_image_to_item(self, doc, file_path):
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
    
    
    img_count = frappe.db.sql("""
                SELECT tf.attached_to_name
                FROM tabFile tf 
                WHERE tf.attached_to_doctype = "Item" AND tf.attached_to_name = %s
            """,(doc.name), as_dict=True)
    
    
    
    position = 1
    if self.attached_to_field == 'image':
        types = ["image", "small_image", "thumbnail"]
        position = 1
    else:
        types = []
        position = len(img_count)
    
    
    base_url, headers = base_data("magento")
    data = {
        "entry": {
            "media_type": "image",
            "label": "",
            "position": position,
            "disabled": False,
            "types": types,
            "content": {
                "base64_encoded_data": encoded_image,
                "type": "image/jpeg",
                "name": image
            }
        }
    }
        
    url = base_url + f"/rest/V1/products/{doc.item_code}/media"

    response =  request_with_history(
                    req_method='POST', 
                    document=self.doctype, 
                    doctype=self.name, 
                    url=url, 
                    headers=headers  ,
                    payload=data        
                )
    
    if response.status_code == 200:
        frappe.msgprint("Image Added to Item Successfully", alert = True, indicator = 'green')
    else:
        frappe.throw(f"Error Image: {response.text}")
        
        
@frappe.whitelist()
def get_magento_image_id(self, image_path):
    base_url, headers = base_data("magento")
    
    url = base_url + f"/rest/default/V1/products/{self.item_code}/media"
    
    response = request_with_history(
                    req_method='GET', 
                    document=self.doctype, 
                    doctype=self.name, 
                    url=url, 
                    headers=headers  ,
                )
    if response.status_code == 200:
        image_data = response.json()
    else:
        frappe.throw(f"Error Deleting Image: {response.text}")
    
    entity_id = None
    for data in image_data:
        magento_filename = data['file'].split('/')[-1]
        if magento_filename == image_path:
            entity_id = data['id']
    if entity_id:
        remove_image_from_magento(self, entity_id)
    else:
        frappe.throw("The image is not found in Magento.")
            
    
@frappe.whitelist()
def remove_image_from_magento(self, entity_id):
    base_url, headers = base_data("magento")
    url = base_url + f"/rest/V1/products/{self.item_code}/media/{entity_id}"
    response = request_with_history(
                    req_method='DELETE', 
                    document=self.doctype, 
                    doctype=self.name, 
                    url=url, 
                    headers=headers        
                )    
    if response.status_code == 200:
        frappe.msgprint("Image Deleted Successfully From Magento", alert = True, indicator = 'green')
    else:
        frappe.throw(f"Error Deleting Image: {response.text}")
                
