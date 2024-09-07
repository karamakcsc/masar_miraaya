import frappe
import json
import requests
from masar_miraaya.api import base_request_magento_data

def validate(self, method):
    if self.custom_is_publish and self.custom_created_in_frappe:
        create_new_customer_group(self)
    pass
    
def create_new_customer_group(self):
    try:
        base_url, headers = base_request_magento_data()
        url = base_url + "/rest/V1/customerGroups"
            
        data = {
                "group": {
                    "code": self.customer_group_name,
                    "tax_class_id": 3,
                }
            }

        if self.is_new() == 1:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                json_response = response.json()
                customer_group_id = json_response['id']
                self.custom_customer_group_id = customer_group_id
                frappe.msgprint(f"Customer Group Created Successfully in Magento")
            else:
                frappe.throw(f"Failed To Create Customer Group in Magento: {str(response.text)}")
        else:
            url = base_url + f"/rest/V1/customerGroups/{self.custom_customer_group_id}"
            
            data = {
                "group": {
                    "code": self.name,
                    "tax_class_id": 3,
                }
            }
            
            response = requests.put(url, headers=headers, json=data)
            
            if response.status_code == 200:
                frappe.msgprint("Customer Group Updated Successfully in Magento")
            else:
                frappe.throw(f"Failed to Update Customer Group in Magento: {str(response.text)}")

    except Exception as e:
        frappe.throw(f"Failed to create customer group: {str(e)}")