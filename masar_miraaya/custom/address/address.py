import frappe
import requests
from masar_miraaya.api import base_data

def validate(self, method):
    update_customer_address(self)

def update_customer_address(self):
    customer_name = None
    customer_id = None
    if self.links:        
        for link in self.links:
            if link.link_doctype == "Customer":
                customer_name = link.link_name
                break
                
    if not customer_name:
        return
    
    customer_sql = frappe.db.sql("SELECT custom_customer_id, custom_is_publish FROM tabCustomer WHERE name = %s", (customer_name), as_dict=True)
    if customer_sql and customer_sql[0] and customer_sql[0]['custom_is_publish'] and customer_sql[0]['custom_customer_id']:
        if customer_sql[0]['custom_is_publish'] != 1:
            return
        
        customer_id = customer_sql[0]['custom_customer_id']
    
    if customer_id in ['', None, ' ', 0]:
        return
                    
    counrty_id_sql = frappe.db.sql("SELECT code FROM tabCountry WHERE name = %s" , (self.country) , as_dict = True)
    if counrty_id_sql and counrty_id_sql[0] and counrty_id_sql[0]['code']:
        country_id = counrty_id_sql[0]['code']  
                        
    address_sql = frappe.db.sql("""
                                    SELECT 
                                        ta.address_line1, ta.custom_address_id, ta.city, ta.country, ta.pincode,
                                        ta.custom_first_name, ta.custom_last_name, 
                                        ta.phone, ta.is_primary_address, ta.is_shipping_address
                                    FROM tabAddress ta
                                    INNER JOIN `tabDynamic Link` tdl ON tdl.parent = ta.name
                                    INNER JOIN tabCustomer tc ON tc.name = tdl.link_name
                                    WHERE tdl.link_doctype = 'Customer' AND tc.name = %s
                                """, (customer_name), as_dict=True)
    address_list = []
    if len(address_sql) != 0:
        for address in address_sql:
            if self.custom_address_id != address['custom_address_id']:
                address_list.append({
                    "customer_id": customer_id,
                    "street": [address['address_line1']],
                    "country_id": country_id.upper(),
                    "telephone": address['phone'],
                    "postcode": address['pincode'],
                    "city": address['city'],
                    "firstname": address['custom_first_name'],
                    "lastname": address['custom_last_name'],
                })
    
    address_list.append({
        "customer_id": customer_id,
        # "region": {
        #     "region_code": "string",
        # #    "region": "string",
        #     "region_id": 0,
        # },
        "street": [self.address_line1],
        "country_id": country_id.upper(),
        "telephone": self.phone,
        "postcode": self.pincode,
        "city": self.city,
        "firstname": self.custom_first_name,
        "lastname": self.custom_last_name,
        # "default_shipping": True if self.is_shipping_address else False, ## if send address send without default_shipping and default_billing
        # "default_billing": True if self.is_primary_address else False    ## to stop error
    })
    
    # frappe.throw(str(address_list))
    
    base_url, headers = base_data("magento")
    url = base_url + f"/rest/V1/customers/{customer_id}"
    
    data = {
        "customer": {
            "addresses": address_list
        }
    }
    
    response = requests.put(url, headers=headers, json=data)
    if response.status_code == 200:
        json_response = response.json()
        addresses = json_response['addresses'][0]
        address_id = addresses['id']
        self.custom_address_id = address_id
        frappe.msgprint(f"Customer Address Updated Successfully in Magento", alert = True, indicator = 'green')
    else:
        frappe.throw(f"Failed to Update Customer Address in Magento: {str(response.text)}")