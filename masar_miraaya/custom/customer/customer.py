import frappe
import json
import requests
from masar_miraaya.api import base_data
from frappe import _
def validate(self, method):
    # check_validation(self)
    roles = (frappe.get_roles(frappe.session.user))
    if (self.custom_is_publish and ('API Integration' not in roles)) or (self.custom_is_publish and frappe.session.user == 'Administrator' ):
        magento = frappe.get_doc('Magento Sync')
        if magento.sync == 0 :
            create_new_customer(self)
        else: 
            frappe.throw("Set Sync in Magento Sync disabled. To Update/Create in magento.")
    
def create_new_customer(self):
    # try:
        base_url, headers = base_data("magento")
        url = base_url + f"/rest/V1/customers/{self.custom_customer_id}"
            
        gender = {
            'Male': 1,
            'Female': 2,
        }.get(self.gender, 0)
        
        if not self.customer_group:
            frappe.throw("Customer Group is Mandatory")
        
        
        ### Send the address empty until fix in Magento 2 customer address or send it without default billing and default shipping
        
        address_sql = frappe.db.sql(""" SELECT 
                                            ta.address_line1, ta.custom_address_id, ta.city, ta.country, ta.pincode,
                                            ta.custom_first_name, ta.custom_last_name, 
                                            ta.phone, ta.is_primary_address, ta.is_shipping_address 
                                        FROM tabAddress ta 
                                        INNER JOIN `tabDynamic Link` tdl ON tdl.parent = ta.name 
                                        WHERE tdl.link_doctype = 'Customer' AND tdl.link_name = %s
                                    """, (self.name), as_dict=True)
        
        address_data = []
        
        if address_sql:
            for address in address_sql:
                counrty_id_sql = frappe.db.sql("SELECT code FROM tabCountry WHERE name = %s" , (address_sql[0]['country']) , as_dict = True)
                if counrty_id_sql and counrty_id_sql[0] and counrty_id_sql[0]['code']:
                    country_id = counrty_id_sql[0]['code'].upper()
                
                address_id = address['custom_address_id']
                is_address_shipping = address['is_shipping_address']
                is_address_billing = address['is_primary_address']
                address_data.append({
                    "customer_id": self.custom_customer_id,
                    "street": [address['address_line1']],
                    "country_id": country_id,
                    "telephone": address['phone'],
                    "postcode": address['pincode'],
                    "city": address['city'],
                    "firstname": address['custom_first_name'],
                    "lastname": address['custom_last_name'],
                    # "default_shipping": True if is_address_shipping == 1 else False,
                    # "default_billing": True if is_address_billing == 1 else False
                })
                
                # frappe.throw(str(address_data))
        
        data = {
            "customer": {
                "group_id": self.custom_customer_group_id,
                # "default_billing": str(address_id) if is_address_billing == 1 else "0", ### automatically fill the default_billing, default_shipping ids
                # "default_shipping": str(address_id) if is_address_shipping == 1 else "0",
                "email": self.custom_email,
                "firstname": self.custom_first_name,
                "middlename": self.custom_middle_name,
                "lastname": self.custom_last_name,
                "prefix": self.custom_prefix,
                "suffix": self.custom_suffix,
                "dob": self.custom_date_of_birth,
                "gender": gender,
                "store_id": 1,
                "website_id": 1,
                "addresses": address_data,
                "disable_auto_group_change": 0,
                "extension_attributes": {
                    "is_subscribed": True if self.custom_is_subscribed else False
                }
            }
        }
        response = requests.put(url, headers=headers, json=data)
        if response.status_code == 200:
            json_response = response.json()
            customer_id = json_response['id']
            # address = json_response['addresses'][0]
            # address_id = address['id']
            # default_billing = json_response['default_billing']
            # default_shipping = json_response['default_shipping']
            self.custom_customer_id = customer_id
            # self.custom_address_id = address_id
            # self.custom_default_shipping_id = default_shipping
            # self.custom_default_billing_id = default_billing
            frappe.msgprint(f"Customer Created/Updated Successfully in Magento", alert = True, indicator = 'green')
        else:
            frappe.throw(f"Failed to Create/Update Customer in Magento: {str(response.text)}")
    # except Exception as e:
    #     frappe.throw(f"Failed to create customer: {str(e)}")
        
        
def check_validation(self):
    total_options_selected = (self.custom_is_delivery + self.custom_is_payment_channel + self.custom_is_digital_wallet)
    if total_options_selected  > 1:
        frappe.throw("Please select only one option: Delivery, Payment Channel, or Digital Wallet." , title= _("Validation Error"))
    elif total_options_selected == 1:
        if  self.customer_group:
            group_doc = frappe.get_doc('Customer Group' , self.customer_group)
            if self.custom_is_delivery:
                if not group_doc.custom_is_delivery: 
                    frappe.throw("The selected Customer Group must support Delivery.")
            elif self.custom_is_payment_channel:
                if not group_doc.custom_is_payment_channel:
                    frappe.throw("The selected Customer Group must support Payment Channel.")
            elif self.custom_is_digital_wallet:
                if not group_doc.custom_is_digital_wallet:
                    frappe.throw("The selected Customer Group must support Digital Wallet.")
                    