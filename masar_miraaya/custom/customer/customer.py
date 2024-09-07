import frappe
import json
import requests
from masar_miraaya.api import base_request_magento_data

def validate(self, method):
    if self.custom_is_publish and self.custom_created_in_frappe:
        create_new_customer(self)
    pass
    
def create_new_customer(self):
    try:
        base_url, headers = base_request_magento_data()
        url = base_url + "/rest/V1/customers"
            
        gender = {
            'Male': 1,
            'Female': 2,
        }.get(self.gender, 0)
        
        data = {
            "customer": {
                "group_id": self.custom_customer_group_id,
                "email": self.custom_email,
                "firstname": self.custom_first_name,
                "middlename": self.custom_middle_name,
                "lastname": self.custom_last_name,
                "prefix": self.custom_prefix,
                "suffix": self.custom_suffix,
                "dob": self.custom_date_of_birth,
                "gender": gender,
                "store_id": self.custom_store_id,
                "website_id": self.custom_website_id,
                "addresses": [
                        {
                            "customer_id": self.custom_customer_id,
                            "street": [
                                self.custom_street
                            ],
                            "firstname": self.custom_address_first_name,
                            "lastname": self.custom_address_last_name,
                            "default_shipping": True if self.custom_is_shipping_address else False,
                            "default_billing": True if self.custom_is_primary_address else False
                        }
                    ],
                "disable_auto_group_change": 0,
                "extension_attributes": {
                    "is_subscribed": True if self.custom_is_subscribed else False
                }
            }
        }
        if self.is_new() == 1:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                json_response = response.json()
                customer_id = json_response['id']
                self.custom_customer_id = customer_id
                frappe.msgprint("Customer Created Successfully in Magento")
            else:
                frappe.throw(f"Failed to Create Customer in Magento: {str(response.text)}")
                
        else:
            url = base_url + f"/rest/V1/customers/{self.custom_customer_id}"
            
            data = {
                "customer": {
                    "group_id": self.custom_customer_group_id,
                    "email": self.custom_email,
                    "firstname": self.custom_first_name,
                    "middlename": self.custom_middle_name,
                    "lastname": self.custom_last_name,
                    "prefix": self.custom_prefix,
                    "suffix": self.custom_suffix,
                    "dob": self.custom_date_of_birth,
                    "gender": gender,
                    "store_id": self.custom_store_id,
                    "website_id": self.custom_website_id,
                    "addresses": [],
                    "disable_auto_group_change": 0,
                    "extension_attributes": {
                        "is_subscribed": True if self.custom_is_subscribed else False
                    }
                }
            }
            
            response = requests.put(url, headers=headers, json=data)
            
            if response.status_code == 200:
                frappe.msgprint("Customer Updated Successfully in Magento")
            else:
                frappe.throw(f"Failed to Update Customer in Magento: {str(response.text)}")
    except Exception as e:
        frappe.throw(f"Failed to create customer: {str(e)}")

        
@frappe.whitelist()
def get_customer_group_id(group_id):
    query = frappe.db.sql(f"""
                         SELECT custom_customer_group_id FROM `tabCustomer Group` WHERE name = '{group_id}'
                         """, as_dict=True)
    parent_group_id = query[0]['custom_customer_group_id']
    return parent_group_id