import frappe
import requests
from datetime import datetime
from masar_miraaya.api import base_request_magento_data



@frappe.whitelist()
def get_customer_group_name(id):
    query = frappe.db.sql(f"""
                         SELECT customer_group_name FROM `tabCustomer Group` WHERE custom_customer_group_id = {id}
                         """, as_dict=True)
    customer_group = query[0]['customer_group_name']
    return customer_group

@frappe.whitelist()  
def get_magento_customers():
    try:
        base_url, headers = base_request_magento_data()
        url = base_url + "/rest/V1/customers/search?searchCriteria="
        request = requests.get(url, headers=headers)
        json_response = request.json()
        customers = json_response['items']
        customer_list = []

        for customer in customers:
            customer_id = customer['id']
            customer_group_id = customer['group_id']
            customer_group_name = get_customer_group_name(customer_group_id)
            customer_first_name = customer['firstname']
            customer_last_name = customer['lastname']
            
            # if customer['dob']:
            #     customer_dob = customer['dob']
            # else:
            #     customer_dob = ""
            full_name = " ".join([customer_first_name, customer_last_name])
            customer_email = customer['email']
            customer_gender = customer['gender']
            
            if customer_gender == 1:
                customer_gender = "Male"
            elif customer_gender == 2:
                customer_gender = "Female"
            else:
                customer_gender = ""
                
            # customer_list.append(customer_dob)
                
            existing_customers = frappe.db.sql("Select name FROM `tabCustomer` WHERE name = %s",(full_name), as_dict = True)
            if not (existing_customers and existing_customers[0] and existing_customers[0]['name']):
                new_customer = frappe.new_doc('Customer')
                new_customer.custom_customer_id = customer_id
                new_customer.customer_name = full_name
                new_customer.custom_first_name = customer_first_name
                new_customer.custom_last_name = customer_last_name
                new_customer.custom_email = customer_email
                new_customer.customer_group = customer_group_name
                new_customer.gender = customer_gender
                new_customer.custom_customer_group_id = customer_group_id
                # new_customer.custom_date_of_birth = customer_dob
                new_customer.save(ignore_permissions = True)

            
            adresses = customer['addresses']
            for address in adresses:
                address_id = address['id']
                # address_type = address['address_type'].title()
                address_line = address['street'][0]
                country = address['region']['region']
                city = address['city']
                pincode = address['postcode']
                phone = address['telephone']
                email_id = customer_email
                full_name = f"{address['firstname']} {address['lastname']}"
                # address_name = 
                # existing_addresses = frappe.db.sql("Select name FROM `tabAddress` WHERE name = %s",(full_name), as_dict = True)
                # if not (existing_addresses and existing_addresses[0] and existing_addresses[0]['name']):
                new_address = frappe.new_doc("Address")
                new_address.custom_address_id = address_id
                # new_address.address_type = address_type
                new_address.address_line1 = address_line
                new_address.county = country
                new_address.city = city
                new_address.pincode = pincode
                new_address.phone = phone
                new_address.email_id = email_id
                new_address.is_shipping_address = 1
                new_address.is_primary_address = 1
                new_address.append('links', {
                        'link_doctype': "Customer",
                        'link_name': full_name
                    })
                new_address.save(ignore_permissions = True)
                
        return "customer_list"
    except Exception as e:
        return f"Error get customers: {e}"