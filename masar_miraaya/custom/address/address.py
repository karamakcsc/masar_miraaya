import frappe
import requests
from masar_miraaya.api import base_data

def validate(self, method):
    update_customer_address(self)

def update_customer_address(self):
    try:
        if not self.links:
            frappe.throw("Link this address to a customer in the child table.")
        
        for link in self.links:
            if link.link_doctype == "Customer":
                customer_name = link.link_name
            else:
                frappe.throw("No linked customer in the child table.")
                
        customer_sql = frappe.db.sql("SELECT custom_customer_id, custom_is_publish FROM tabCustomer WHERE name = %s", (customer_name), as_dict=True)
        if customer_sql and customer_sql[0] and customer_sql[0]['custom_is_publish'] and customer_sql[0]['custom_customer_id']:
            if customer_sql[0]['custom_is_publish'] != 1:
                frappe.throw("The Customer Must be Publish to Magento")
            else:
                customer_id = customer_sql[0]['custom_customer_id']
        
        counrty_id_sql = frappe.db.sql("SELECT code FROM tabCountry WHERE name = %s" , (self.country) , as_dict = True)
        if counrty_id_sql and counrty_id_sql[0] and counrty_id_sql[0]['code']:
            country_id = counrty_id_sql[0]['code']        
        
        base_url, headers = base_data("magento")
        url = base_url + f"/rest/V1/customers/{customer_id}"
        
        data = {
            "customer": {
                "addresses": [
                    {
                        "customer_id": customer_id,
                        # "region": {
                        #     "region_code": "string",
                        #     "region": "string",
                        #     "region_id": 0,
                        # },
                        "street": [
                            self.address_line1
                        ],
                        "country_id": country_id.upper(),
                        "telephone": self.phone,
                        "postcode": self.pincode,
                        "city": self.city,
                        "firstname": self.custom_first_name,
                        "lastname": self.custom_last_name,
                        "default_shipping": True if self.is_shipping_address else False,
                        "default_billing": True if self.is_primary_address else False
                    }
                ]
            }
        }
        
        # frappe.throw(str(data))
        response = requests.put(url, headers=headers, json=data)
        if response.status_code == 200:
            json_response = response.json()
            address = json_response['addresses'][0]
            address_id = address['id']
            self.custom_address_id = address_id
            frappe.msgprint(f"Customer Address Updated Successfully in Magento: {str(response.text)}")
        else:
            frappe.throw(f"Failed to Update Customer Address in Magento: {str(response.text)}")
    except Exception as e:
        frappe.throw(f"Failed to update customer address: {str(e)}")