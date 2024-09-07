import frappe
import requests
import json
import base64
import os
from masar_miraaya.api import base_request_magento_data
from masar_miraaya.custom.item.item import add_image_to_item, remove_image_from_magento, get_magento_image_id


def validate(self, method):
    if self.attached_to_doctype == 'Item':
        doc = frappe.get_doc('Item', self.attached_to_name)
        file_path = self.file_url
        add_image_to_item(doc, file_path)

def on_trash(self, method):
    if self.attached_to_doctype == 'Item':
        doc = frappe.get_doc('Item', self.attached_to_name)
        get_magento_image_id(doc, self.file_name)
        # remove_image_from_magento(doc)
    # frappe.throw("Success")

# @frappe.whitelist()
# def add_image_to_item(self):
#     try:
#         image_path = self.image
#         image = image_path.split("files/")[1]
#         bench_path = frappe.utils.get_bench_path()
#         site_name = frappe.utils.get_site_name(frappe.local.site)
#         file_path = os.path.join(bench_path, 'sites', site_name, 'public', 'files', image)
#         with open(file_path, "rb") as image_file:
#                 encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
#         base_url, headers = base_request_magento_data()
#         data = {
#             "entry": {
#                 "media_type": "image",
#                 "label": "",
#                 "position": 1,
#                 "disabled": False,
#                 "types": [
#                     "image",
#                     "small_image",
#                     "thumbnail",
#                     "swatch_image"
#                 ],
#                 "content": {
#                     "base64_encoded_data": encoded_image,
#                     "type": "image/jpeg",
#                     "name": image
#                 }
#             }
#         }
#         url = base_url + f"/rest/V1/products/{self.item_code}/media"
    
    
#         response = requests.post(url, headers=headers, json=data)
#         if response.status_code == 200:
#             frappe.msgprint("Image Added to Item Successfully")
#         else:
#             frappe.throw(str(f"Error Image: {response.text}"))
#     except Exception as e:
#         frappe.throw(f"Failed to create item in Magento: {str(e)}")