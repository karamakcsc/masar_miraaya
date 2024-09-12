import frappe
import json
import requests
from masar_miraaya.api import base_data

def validate(self, method):

    if self.custom_is_publish:
        magento = frappe.get_doc('Magento Sync')
        if magento.sync == 0 :
            create_new_customer(self)
        else: 
            frappe.throw("Set Sync in Magento Sync disabled. To Update/Create in magento.")
    
def create_new_customer(customer_name):
    doc = frappe.get_doc('Customer', customer_name)
    try:
        base_url, headers = base_data("magento")
        url = base_url + "/rest/V1/customers"
            
        gender = {
            'Male': 1,
            'Female': 2,
        }.get(doc.gender, 0)
        
        data = {
            "customer": {
                "group_id": doc.custom_customer_group_id,
                "email": doc.custom_email,
                "firstname": doc.custom_first_name,
                "middlename": doc.custom_middle_name,
                "lastname": doc.custom_last_name,
                "prefix": doc.custom_prefix,
                "suffix": doc.custom_suffix,
                "dob": doc.custom_date_of_birth,
                "gender": gender,
                "store_id": doc.custom_store_id,
                "website_id": doc.custom_website_id,
                "addresses": [
                        {
                            "customer_id": doc.custom_customer_id,
                            "street": [
                                doc.custom_street
                            ],
                            "country_id": doc.custom_country_id,
                            "telephone": doc.custom_phone,
                            "postcode": doc.custom_pincode,
                            "city": doc.custom_city,
                            "firstname": doc.custom_address_first_name,
                            "lastname": doc.custom_address_last_name,
                            "default_shipping": True if doc.custom_is_shipping_address else False,
                            "default_billing": True if doc.custom_is_primary_address else False
                        }
                    ],
                "disable_auto_group_change": 0,
                "extension_attributes": {
                    "is_subscribed": True if doc.custom_is_subscribed else False
                }
            }
        }
        if doc.is_new() == 1:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                json_response = response.json()
                customer_id = json_response['id']
                address = json_response['addresses'][0]
                address_id = address['id']
                doc.custom_customer_id = customer_id
                doc.custom_address_id = address_id
                frappe.msgprint("Customer Created Successfully in Magento")
            else:
                frappe.throw(f"Failed to Create Customer in Magento: {str(response.text)}")
                
        else:
            url = base_url + f"/rest/V1/customers/{doc.custom_customer_id}"
            
            data = {
                "customer": {
                    "group_id": doc.custom_customer_group_id,
                    "email": doc.custom_email,
                    "firstname": doc.custom_first_name,
                    "middlename": doc.custom_middle_name,
                    "lastname": doc.custom_last_name,
                    "prefix": doc.custom_prefix,
                    "suffix": doc.custom_suffix,
                    "dob": doc.custom_date_of_birth,
                    "gender": gender,
                    "store_id": doc.custom_store_id,
                    "website_id": doc.custom_website_id,
                    "addresses": [
                        {
                            "customer_id": doc.custom_customer_id,
                            "street": [
                                doc.custom_street
                            ],
                            "country_id": doc.custom_country_id,
                            "telephone": doc.custom_phone,
                            "postcode": doc.custom_pincode,
                            "city": doc.custom_city,
                            "firstname": doc.custom_address_first_name,
                            "lastname": doc.custom_address_last_name,
                            "default_shipping": True if doc.custom_is_shipping_address else False,
                            "default_billing": True if doc.custom_is_primary_address else False
                        }
                    ],
                    "disable_auto_group_change": 0,
                    "extension_attributes": {
                        "is_subscribed": True if doc.custom_is_subscribed else False
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