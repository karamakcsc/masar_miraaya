import frappe
import json
import requests
from masar_miraaya.api import base_request_magento_data

def after_save(self, method):
    # if self.custom_is_publish:
    create_new_customer(self)
    pass
    
def create_new_customer(self):
    base_url, headers = base_request_magento_data()
    url = base_url + "/rest/V1/customers"
        
    # is_active = 0

    # if self.custom_is_publish == 1:
    #     is_active = 1
    # else:
    #     is_active = 0

    data = {
        
        "customer": {
            "group_id": self.custom_customer_group_id,
            "email": self.custom_email,
            "firstname": self.custom_first_name,
            "lastname": self.custom_last_name,
            "gender": 0,
            "store_id": 0,
            "addresses": []
        }
    }
    get_cust_url = base_url + "/rest/V1/customers/search?searchCriteria="
    request = requests.get(get_cust_url, headers=headers)
    json_response = request.json()
    customers = json_response['items']
    customer_email_list = []
    
    for customer in customers:
        customer_email = customer['email']
        customer_email_list.append(customer_email)
    try:
        # if self.is_new() == 1:
        if self.custom_email not in customer_email_list:
            response = requests.post(url, headers=headers, json=data)
            json_response = response.json()
            customer_id = json_response['id']
            self.custom_customer_id = customer_id
            response.raise_for_status()
        else:
            update_customer_if_exists(self, base_url, headers)
    except Exception as e:
        frappe.throw(f"Failed to create or update customer: {str(e)}")

def update_customer_if_exists(self, base_url, headers):
    
    try:

        # is_active = 1

        # if self.custom_is_publish == 0:
        #     is_active = 0
        # else:
        #     is_active = 0

        update_url = base_url + f"/rest/V1/customers/{self.custom_customer_id}"
        update_data = {
            "customer": {
                "id": self.custom_customer_id,
                "email": self.custom_email,
                "firstname": self.custom_first_name,
                "lastname": self.custom_last_name,
                "gender": 0,
                "store_id": 0,
                "addresses": []
            }
        }
        update_response = requests.put(update_url, headers=headers, json=update_data)
        update_response.raise_for_status()
            
    except Exception as e:
        frappe.throw(f"Failed to update customer: {str(e)}")
        
@frappe.whitelist()
def get_customer_group_id(group_id):
    query = frappe.db.sql(f"""
                         SELECT custom_customer_group_id FROM `tabCustomer Group` WHERE name = '{group_id}'
                         """, as_dict=True)
    parent_group_id = query[0]['custom_customer_group_id']
    return parent_group_id