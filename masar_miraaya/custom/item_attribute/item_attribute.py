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
    # try:
        if self.custom_attribute_code == 'color':
            attribute_id = 93   
        elif self.custom_attribute_code == 'shade':
            attribute_id = 159  
        elif self.custom_attribute_code == 'size':
            attribute_id = 144 
        elif self.custom_attribute_code == 'size_ml':
            attribute_id = 158
        else:
            frappe.throw("Only can create in 'Size', 'Size (ml)', 'Color' and 'Shade'.")
        base_url, headers = base_data("magento")        
        url = base_url + f"/rest/V1/products/attributes/{attribute_id}"
        
        get_response = requests.get(url, headers=headers)
        if get_response.status_code == 200:
            json_response = get_response.json()
            options = json_response['options']
            existing_list = []
            unexisting_list = []
            for option in options:
                existing_list.append(option['label'])
            
            for row in self.item_attribute_values:
                if row.attribute_value not in existing_list and row.attribute_value != 'Default':
                    unexisting_list.append(row.attribute_value)
            options_list = []
            if unexisting_list:
                for value in unexisting_list:
                    options_dict = {
                        "label": value,
                        "value": value 
                    }
                    options_list.append(options_dict)
                data = {
                    "attribute": {
                        "attribute_id":attribute_id,
                        "attribute_code": self.custom_attribute_code,
                        "frontend_input": "select",
                        "entity_type_id": "4",
                        "is_required": False,
                        "options": options_list
                    }
                }
                
                response = requests.put(url, headers=headers, json=data)
                if response.status_code == 200:
                    json_response = response.json()
                    options = json_response['options']
                    for row in self.item_attribute_values:
                        for option in options:
                            if option['label'] == row.attribute_value and option['value'] != row.abbr:
                                row.abbr = option['value']
                                frappe.msgprint(f"Attribute '{row.attribute_value}' created successfully in Magento.", alert=True, indicator='green')
                                break
                else:
                    frappe.throw(f"Failed to Create Attribute in Magento: {str(response.text)}")
    # except Exception as e:
    #     frappe.throw(f"Failed to create Attribute: {str(e)}")