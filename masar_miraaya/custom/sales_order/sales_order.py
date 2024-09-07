import frappe
import requests
import pycountry
from datetime import date
from masar_miraaya.api import base_request_magento_data


def on_submit(self, method):
    create_magento_sales_order(self)

@frappe.whitelist()
def create_magento_sales_order(self):
    base_url, headers = base_request_magento_data()
    
    try:
        customer_doc = frappe.get_doc('Customer', self.customer)
        customer_first_name = customer_doc.custom_first_name
        customer_last_name = customer_doc.custom_last_name
        customer_email = customer_doc.custom_email
        customer_id = customer_doc.custom_customer_id
        customer_store_id = customer_doc.custom_store_id
        customer_website_id = customer_doc.custom_website_id
        customer_doc_name = customer_doc.name
        
        query = frappe.db.sql(""" 
                            SELECT 
                                    ta.address_line1, ta.city, ta.country, ta.pincode,
                                    ta.phone, ta.custom_country_id, ta.email_id, ta.custom_first_name, ta.custom_last_name 
                            FROM tabAddress ta 
                            WHERE custom_customer_id = %s AND is_primary_address = 1 and is_shipping_address = 1
                            """, (customer_id), as_dict=True)
        
        if query and query[0]:
            for data in query:
                address_line = data['address_line1']
                city = data['city']
                country = data['country']
                pincode = data['pincode']
                phone = data['phone']
                country_id = data['custom_country_id']
                email_id = data['email_id']
                first_name = data['custom_first_name']
                last_name = data['custom_last_name']
                
        item_list = []
        if self.get('items'):
            for item in self.get('items'):
                dict_items = {
                    "name": item.item_name,
                    "sku": item.item_code,
                    "qty_ordered": item.qty,
                    "price": item.amount
                }
                item_list.append(dict_items)
        else:
            frappe.throw("Please Add Items")
            
        payload = {
            "entity": {
                "base_currency_code": self.currency,
                "base_grand_total": self.total,
                "created_at": self.transaction_date,
                "customer_email": customer_email,
                "customer_firstname": customer_first_name,
                "customer_lastname": customer_last_name,
                "grand_total": self.grand_total,
                "order_currency_code": self.currency,
                "status": self.custom_sales_order_status.lower(),
                "store_id": customer_store_id,
                "subtotal": self.grand_total,
                "total_qty_ordered": self.total_qty,
                "updated_at": self.delivery_date,
                "items": item_list,
                "billing_address": {
                "firstname": first_name,
                "lastname": last_name,
                "street": [
                    address_line
                ],
                "city": city,
                "postcode": pincode,
                "country_id": country_id,
                "telephone": phone
                },
                "payment": {
                "method": "checkmo"
                },
                "extension_attributes": {
                "shipping_assignments": [
                    {
                    "shipping": {
                        "address": {
                        "firstname": first_name,
                        "lastname": last_name,
                        "street": [
                            address_line
                        ],
                        "city": city,
                        "postcode": pincode,
                        "country_id": country_id,
                        "telephone": phone
                        },
                        "method": "flatrate_flatrate"
                    }
                    }
                ]
                }
            }
            }

        
        url = f"{base_url}/rest/V1/orders" 
        
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code in [200, 201, 202, 203]:
            frappe.msgprint("Sales Order Created Successfully in Magento")
        else:
            frappe.throw(str(f"Error Creating Sales Order in Magento: {response.text}"))
    except Exception as e:
        frappe.throw(str(f"Error Creating Sales Order in Magento: {e}"))





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
#             country = get_country_name(address['country_id'])
#             address_type = address['address_type'].title()
#             address_line = address['street'][0]
#             city = address['city']
#             pincode = address['postcode']
#             phone = address['telephone']
#             email_id = address['email']
#             customer_first_name = address['firstname']
#             customer_last_name = address['lastname']
            
#             customer_name_q = frappe.db.sql(""" SELECT name
#                                           FROM `tabCustomer` 
#                                           WHERE custom_first_name = %s AND custom_last_name = %s """, 
#                                           (customer_first_name, customer_last_name), as_dict = True)
#             customer_name = customer_name_q[0]['name']
#             existing_address = frappe.db.sql(
#                 """SELECT name FROM `tabAddress`
#                 WHERE address_line1 = %s AND city = %s AND pincode = %s AND phone = %s AND email_id = %s""",
#                 (address_line, city, pincode, phone, email_id),
#                 as_dict=True
#             )
#             if not (existing_address and existing_address[0] and existing_address[0]['name']):
#                 new_address = frappe.new_doc("Address")
#                 new_address.custom_address_id = address_id
#                 new_address.address_type = address_type
#                 new_address.address_line1 = address_line
#                 new_address.county = country
#                 new_address.city = city
#                 new_address.pincode = pincode
#                 new_address.phone = phone
#                 new_address.email_id = email_id
#                 new_address.is_shipping_address = 1
#                 new_address.append('links', {
#                         'link_doctype': "Customer",
#                         'link_name': full_name
#                     })
#                 new_address.save(ignore_permissions = True)

#         return "Address created successfully"
#     except Exception as e:
#         return f"Error Create Customer Address: {e}"
    
# @frappe.whitelist()
# def create_sales_order():
#     base_url, headers = base_request_magento_data()    
#     try:
#         sales_order = get_magento_sales_order()
#         for order in sales_order:
#             so_items = []
#             customer = order['customer_firstname'] + ' ' + order['customer_lastname']
#             transaction_date = order['created_at'].split('T')[0]
#             sales_order_status = order['status']
#             customer_address = order['billing_address_id']
            
#             for item in order['items']:
#                 item_code = item['sku']
#                 delivery_date = str(date.today())
#                 qty = item['qty_ordered']
#                 rate = item['price']
                
#             # existing_address = frappe.db.sql(
#             #         """SELECT name FROM `tabAddress`
#             #         WHERE address_line1 = %s AND city = %s AND pincode = %s AND phone = %s AND email_id = %s""",
#             #         (address_line, city, pincode, phone, email_id),
#             #         as_dict=True
#             #     )
#             # if not (existing_address and existing_address[0] and existing_address[0]['name']):
#             new_sales_order = frappe.new_doc("Sales Order")
#             new_sales_order.customer = customer
#             new_sales_order.transaction_date = transaction_date
#             new_sales_order.custom_sales_order_status = sales_order_status
#             new_sales_order.append('Items', {
#                     'item_code': item_code,
#                     'delivery_date': delivery_date,
#                     'qty': qty,
#                     'rate': rate
#                 })
#             new_sales_order.save(ignore_permissions = True)
#         return "Sales Orders created successfully"
    
#     except Exception as e:
#         return f"Error creating sales order: {e}"