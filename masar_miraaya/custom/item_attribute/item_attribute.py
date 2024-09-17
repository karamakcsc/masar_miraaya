import frappe
import json
import requests
from masar_miraaya.api import base_data


def validate(self, method):
    if self.custom_publish_to_magento:
        magento = frappe.get_doc('Magento Sync')
        if magento.sync == 0 :  
            create_attributes_in_magento(self)
        else: 
            frappe.throw("Set Sync in Magento Sync disabled. To Update/Create in magento.")

@frappe.whitelist()
def create_attributes_in_magento(self):
    try:
        if self.custom_attribute_code == 'color':
            attribute_id = 93   
        elif self.custom_attribute_code == 'shade':
            attribute_id = 159  
        elif self.custom_attribute_code == 'size':
            attribute_id = 144 
        elif self.custom_attribute_code == 'size_ml':
            attribute_id = 158
        else:
            attribute_id = None
        base_url, headers = base_data("magento")        
        url = base_url + f"/rest/V1/products/attributes/{attribute_id}"
        
        get_response = requests.get(url, headers=headers)
        if response.status_code == 200:
                    json_response = response.json()
                    options = json_response['options']
                    for option in options:
                        for row in self.item_attribute_values:
                            if option['label'] != row.attribute_value:
                                data = {
                                    "attribute": {
                                        "attribute_id":attribute_id,
                                        "attribute_code": self.custom_attribute_code,
                                        "frontend_input": "select",
                                        "entity_type_id": "4",
                                        "is_required": False,
                                        "options": [
                                            {
                                                "label": row.attribute_value,
                                                "value": row.abbr if row.abbr else row.attribute_value.lower()
                                            }
                                        ]
                                    }
                                }
                                response = requests.put(url, headers=headers, json=data)
                                if response.status_code == 200:
                                    json_response = response.json()
                                    options = json_response['options']
                                    for option in options:
                                        if option['label'] == row.attribute_value:
                                            value = option['value']
                                    row.abbr = value
                                    frappe.msgprint(f"Attribute '{row.attribute_value}' Created Successfully in Magento")
                                else:
                                    frappe.throw(f"Failed to Create Attribute in Magento: {str(response.text)}")
    except Exception as e:
        frappe.throw(f"Failed to create Attribute: {str(e)}")

