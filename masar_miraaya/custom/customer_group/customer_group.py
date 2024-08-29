import frappe
import json
import requests
from masar_miraaya.api import base_request_magento_data

def after_save(self, method):
    # if self.custom_is_publish:
    #     create_new_customer_group(self)
    pass
    
def create_new_customer_group(self):
    base_url, headers = base_request_magento_data()
    url = base_url + "/rest/V1/customerGroups"
        
    data = {
            "group": {
                "code": self.customer_group_name,
                "tax_class_id": 3,
            }
        }
    
    get_cust_group_url = base_url + "/rest/V1/customerGroups/search?searchCriteria="
    request = requests.get(get_cust_group_url, headers=headers)
    json_response = request.json()
    customer_groups = json_response['items']
    customer_group_name_list = []
    for group in customer_groups:
        customer_group_name = group['code']
        customer_group_name_list.append(customer_group_name)

    try:
        if self.name not in customer_group_name_list:
            response = requests.post(url, headers=headers, json=data)
            json_response = response.json()
            customer_group_id = json_response['id']
            self.custom_customer_group_id = customer_group_id
            response.raise_for_status()

    except Exception as e:
        frappe.throw(f"Failed to create customer group: {str(e)}")