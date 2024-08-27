# import frappe
# import json
# import requests
# import pycountry
# from masar_miraaya.api import base_request_magento_data
# from masar_miraaya.api import base_request_data

# @frappe.whitelist()
# def get_magento_sales_order():
#     base_url, headers = base_request_magento_data()
#     try:
#         response = requests.get(f'{base_url}/rest/V1/orders?searchCriteria', headers=headers)
#         json_response = response.json()
#         sales_order = json_response['items']
#         return sales_order
#     except Exception as e:
#         return f"Error Get Sales Order: {e}"
    
# @frappe.whitelist()
# def get_customer_address():
#     magento_so = get_magento_sales_order()
#     try:
#         addresses = []
#         for address in magento_so:
#             billing_address = address['billing_address']
#             addresses.append(billing_address)
                    
#         return addresses
#     except Exception as e:
#         return f"Error Get Customer Address: {e}"

# def get_country_name(country_code):
#     response = requests.get(f'https://restcountries.com/v3.1/alpha/{country_code}')
#     if response.status_code == 200:
#         data = response.json()
#         return data[0]['name']['common']
#     return "Unknown Country"

# @frappe.whitelist()
# def create_customer_address():
#     magento_addresses = get_customer_address()
#     base_url, headers = base_request_data()
#     try:
#         results = []
#         for address in magento_addresses:
#             country_name = get_country_name(address['country_id'])
#             address_type = address['address_type'].title()
#             payload = {
#                 "doctype": "Address",
#                 "address_type": address_type,
#                 "address_line1": address['street'][0],
#                 "city": address['city'],
#                 "country": country_name,
#                 "pincode": address['postcode'],
#                 "phone": address['telephone'],
#                 "email_id": address['email'],
#                 "is_shipping_address": 1,
#                 "links": [
#                     {
#                         "link_doctype": "Customer",
#                         "link_name": f"{address['firstname']} {address['lastname']}"
#                     }
#                 ]
#             }
#             response = requests.post(f'{base_url}/Address', headers=headers, json=payload)
#             if response.status_code == 200:
#                 results.append(f"Address created successfully: {response.json()}")
#             else:
#                 results.append(f"Failed to create address: {response.json()}")

#         return results
#     except Exception as e:
#         return f"Error Create Customer Address: {e}"