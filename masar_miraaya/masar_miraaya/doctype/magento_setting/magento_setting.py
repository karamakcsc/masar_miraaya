# Copyright (c) 2024, KCSC and contributors
# For license information, please see license.txt

import frappe
from masar_miraaya.api import base_data , request_with_history
import requests
from frappe.model.document import Document


class MagentoSetting(Document):
    pass
    # @frappe.whitelist()
    # def update_images(self):
    #     base_url, headers = base_data("magento")
    #     all_items_sql = frappe.db.sql("""
	# 		SELECT name
	# 		FROM `tabItem`
	# 		WHERE name = 'Test Image ERP'
	# 	""", as_dict=True)
        
    #     if all_items_sql:
    #         for item in all_items_sql:
    #             image_in_item_sql = frappe.db.sql("""
    #                     SELECT tf.file_name, name
	# 					FROM tabFile tf 
	# 					WHERE tf.attached_to_doctype = "Item" AND tf.attached_to_name = %s
    #             """,(item.name), as_dict=True)
    #             for image in image_in_item_sql:
    #                 url = base_url + f"/rest/default/V1/products/{item.name}/media"
    #                 response = request_with_history(
	# 								req_method='GET', 
	# 								document=self.doctype, 
	# 								doctype=self.name, 
	# 								url=url, 
	# 								headers=headers  ,
	# 							)
    #                 not_match = []
    #                 if response.status_code == 200:
    #                     image_data = response.json()
    #                     # frappe.throw(str(image_data))
    #                     for image_magento in image_data:
    #                         mag_image = image_magento["file"].split("/")[-1]
    #                         # frappe.throw(f"Image: {mag_image} - {image.file_name}")
    #                         if image.file_name == mag_image:
    #                             frappe.db.set_value("File", image.name, "custom_uploaded_to_magento", 1, update_modified=False )
    #                             frappe.db.commit()
    #                         else:
    #                             not_match.append({
    #                                 "frappe_image": image.file_name,
    #                                 "magento_image": mag_image
	# 								})
    #                         frappe.throw(str(not_match))