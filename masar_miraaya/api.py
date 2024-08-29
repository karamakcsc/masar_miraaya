# from __future__ import unicode_literals
import frappe
import json
import requests
from urllib.parse import urlparse
from io import BytesIO
import base64
import pycountry
from datetime import date
from frappe import _

def base_request_magento_data():
    setting = frappe.get_doc("Magento Setting")
    base_url = str(setting.magento_url).strip()
    headers = {
        "Authorization": f"Bearer {str(setting.magento_auth).strip()}",
        "Content-Type": "application/json"
    }
    return base_url , headers

def base_request_data():
    setting = frappe.get_doc("Magento Setting")
    base_url = str(setting.frappe_url).strip()
    headers = {
        "Authorization": f"Basic {str(setting.frappe_auth).strip()}",
        "Content-Type": "application/json"
    }
    return base_url , headers

def magento_admin_details():
    setting = frappe.get_doc("Magento Setting")
    username = str(setting.username)
    password = str(setting.password)
    
    return username, password

def validate_url(url):
    base_url , headers = base_request_magento_data()
    parsed_url = urlparse(url)
    if not parsed_url.scheme:
        url = f"{base_url}/media/catalog/product" + url
    return url

@frappe.whitelist()
def upload_image_to_frappe(image, item_code):
    if not image:  
        frappe.log_error(f"No image for item: {item_code}", "Image Upload")
        return ''

    try:
        frappe.log_error(f"Uploading image for item: {item_code}", "Image Upload")
        image_url = validate_url(image)
        response = requests.get(image_url)
        response.raise_for_status()

        image_content = BytesIO(response.content).getvalue()
        image_base64 = base64.b64encode(image_content).decode('utf-8')

        file_name = f"{item_code}.jpg"

        _file = frappe.get_doc({
            "doctype": "File",
            "file_name": file_name,
            "attached_to_doctype": "Item",
            "attached_to_name": item_code,
            "is_private": 0,
            "content": image_base64,
            "decode": True
        })
        _file.save()

        return _file.file_url

    except Exception as e:
        frappe.log_error(f"Upload Image Error for item {item_code}: {e}", "Image Upload")
        return f"Upload Image Error: {e}"

@frappe.whitelist()
def get_item_details():
	return frappe.db.sql("""  SELECT *
							FROM `tabItem` ti
							WHERE ti.disabled= 0
							ORDER BY ti.creation DESC; """, as_dict=1)

@frappe.whitelist()
def get_wh_details():
	return frappe.db.sql("""  SELECT *
							FROM `tabWarehouse` tw
							WHERE tw.is_group= 0
							ORDER BY tw.creation DESC; """, as_dict=1)

@frappe.whitelist()
def get_exchange_rate():
		return frappe.db.sql(""" SELECT from_currency, to_currency, exchange_rate
							FROM `tabCurrency Exchange`
							WHERE for_selling =1
							ORDER BY creation DESC;""", as_dict=True)

@frappe.whitelist()
def get_available_qty(item=None, warehouse=None):
    return frappe.db.sql("""
        SELECT tb.warehouse, tb.item_code, (tb.actual_qty - tb.reserved_qty) as `Available Quantity`
        FROM `tabBin` tb
        WHERE tb.item_code = %s AND tb.warehouse = %s
        ORDER BY tb.creation DESC;""",
        (item,warehouse),as_dict=True)
    
@frappe.whitelist()
def create_item_task(item_data):
    item_code = item_data.get('item_code')
    
    existing_item = frappe.db.exists('Item', item_code)
    if existing_item:
        return  
    
    try:
        base_url_frappe, headers_frappe = base_request_data()
        response = requests.post(f"{base_url_frappe}/Item", headers=headers_frappe, json=item_data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        frappe.throw(f"Failed to create item in Frappe: {str(e)}")
        
@frappe.whitelist()
def get_magento_products():
    try:
        base_url, headers = base_request_magento_data()
        url = base_url + "/rest/V1/products?searchCriteria="
        request = requests.get(url, headers=headers)
        json_response = request.json()
        items = json_response['items']

        if items:
            for item in items:
                item_code = item['sku']
                item_name = item['name']
                status = item['status']

                custom_attributes = item['custom_attributes']
                image = None  
                category_id = None 

                description = ""
                item_group = ""

                for attribute in custom_attributes:
                    if attribute['attribute_code'] == 'product_description':
                        description = attribute['value'] if attribute['value'] else ""
                    if attribute['attribute_code'] == 'brand':
                        brand = attribute['value'] if attribute['value'] else ""
                    if attribute['attribute_code'] == 'category_ids':
                        category_id = int(attribute['value'][0])
                        item_group_data = get_magento_categories(category_id)
                        item_group = item_group_data['name']
                    if attribute['attribute_code'] == 'image':
                        image = attribute['value']

                file_url = upload_image_to_frappe(image, item_code) if image else ''
                    
                dict_items = {
                    "naming_series": "STO-ITEM-.YYYY.-",
                    "doctype": "Item",
                    "item_code": item_code,
                    "item_name": item_name,
                    "status": status,
                    "item_group": f"{str(category_id)} - {item_group}",
                    "custom_item_group_id": category_id,
                    "description": description,
                    "brand": brand,
                    "image": file_url,
                    "custom_is_publish": 1
                }

                frappe.enqueue(create_item_task, item_data=dict_items)

        return "Items are being processed"
    except Exception as e:
        frappe.throw(f"General Error: {e}", "Magento Sync")
        return f"General Error: {e}"

@frappe.whitelist()
def get_magento_categories(id=None):
    try:
        base_url, headers = base_request_magento_data()
        if id:
            url = base_url + f"/rest/V1/categories/{id}"
        else:
            url = f"{base_url}/rest/all/V1/categories"
        request = requests.get(url, headers=headers)
        return request.json()
    except Exception as e:
        return f"Get Magento Categories Error: {e}"


@frappe.whitelist()
def create_item_group():
    def process_category(category, parent_name, item_group_name_list):
        category_name = category['name']
        category_id = category['id']
        parent_id = category['parent_id']
        category_status = 1 if category['is_active'] else 0

        unique_name = f"{category_id} - {category_name}"

        existing_item_group = frappe.get_all("Item Group", filters={"item_group_name": unique_name, "parent_item_group": parent_name})
        if existing_item_group:
            return

        payload = {
            "doctype": "Item Group",
            "item_group_name": unique_name,
            "parent_item_group": parent_name,
            "custom_item_group_id": category_id,
            "custom_parent_item_group_id": parent_id,
            "custom_is_publish": 0,
            "is_group": 1 if 'children_data' in category and category['children_data'] else 0
        }

        base_url, headers = base_request_data()

        try:
            response = requests.post(f"{base_url}/Item Group", headers=headers, json=payload)
            response.raise_for_status()
            item_group_name_list.append(unique_name)
        except requests.exceptions.RequestException as e:
            frappe.log_error(f"Failed to create Item Group: {unique_name}, Error: {str(e)}")
            return

        if 'children_data' in category and category['children_data']:
            for child in category['children_data']:
                process_category(child, unique_name, item_group_name_list)

    def update_item_groups_publish_status(item_group_names, publish_status):
        for name in item_group_names:
            frappe.db.set_value("Item Group", {"item_group_name": name}, "custom_is_publish", publish_status)

    try:
        base_url, headers = base_request_data()
        magento_categories = get_magento_categories()
        item_group_name_list = []
        root_category = magento_categories['name']
        root_id = magento_categories['id']
        root_parent_id = magento_categories['parent_id']
        root_status = 1

        root_unique_name = f"{root_id} - {root_category}"

        existing_root_item_group = frappe.get_all("Item Group", filters={"item_group_name": root_unique_name, "parent_item_group": ""})
        if not existing_root_item_group:
            root_payload = {
                "doctype": "Item Group",
                "item_group_name": root_unique_name,
                "parent_item_group": "",
                "custom_item_group_id": root_id,
                "custom_parent_item_group_id": root_parent_id,
                "custom_is_publish": 0,
                "is_group": 1
            }
            
            try:
                response = requests.post(f"{base_url}/Item Group", headers=headers, json=root_payload)
                response.raise_for_status()
                item_group_name_list.append(root_unique_name)
            except requests.exceptions.RequestException as e:
                frappe.log_error(f"Failed to create Root Item Group: {root_unique_name}, Error: {str(e)}")
                return

        all_categories = magento_categories.get('children_data', [])
        for category in all_categories:
            process_category(category, root_unique_name, item_group_name_list)

        update_item_groups_publish_status(item_group_name_list, 1)

        return "Item Groups created successfully"
    except Exception as e:
        return f"Create Item Group Error: {str(e)}"


@frappe.whitelist()  
def get_magento_customers():
    try:
        base_url, headers = base_request_magento_data()
        base_url_frappe, headers_frappe = base_request_data()
        url = base_url + "/rest/V1/customers/search?searchCriteria="
        request = requests.get(url, headers=headers)
        json_response = request.json()
        customers = json_response['items']
        # customer_list = []

        for customer in customers:
            customer_id = customer['id']
            customer_group_id = customer['group_id']
            customer_group_name = get_customer_group_name(customer_group_id)
            customer_first_name = customer['firstname']
            customer_last_name = customer['lastname']
            full_name = " ".join([customer_first_name, customer_last_name])
            customer_email = customer['email']
            # customer_gender = customer['gender']
            url_frappe = base_url_frappe + f"/Customer"
            
            payload = {
                "doctype": "Customer",
                "naming_series": "CUST-.YYYY.-",
                "custom_customer_id": customer_id,
                "customer_name": full_name,
                "custom_first_name": customer_first_name,
                "custom_last_name": customer_last_name,
                "custom_email": customer_email,
                "customer_group": customer_group_name,
                "custom_customer_group_id": customer_group_id
            }

            # customer_list.append(payload)
            
            request_f = requests.post(url_frappe, headers=headers_frappe, json=payload)
            
        return request_f.text
    except Exception as e:
        return f"Error get customers: {e}"
    
@frappe.whitelist()
def get_customer_group():
    try:
        base_url, headers = base_request_magento_data()
        base_url_frappe, headers_frappe = base_request_data()
        url = base_url + "/rest/V1/customerGroups/search?searchCriteria="
        request = requests.get(url, headers=headers)
        json_response = request.json()
        customer_groups = json_response['items']
        
        for group in customer_groups:
            customer_group_id = group['id']
            customer_group_name = group['code']
            
            url_frappe = base_url_frappe + f"/Customer Group"
            payload = {
                    "doctype": "Customer Group",
                    "custom_customer_group_id": customer_group_id,
                    "customer_group_name": customer_group_name,
                }
                
            request_f = requests.post(url_frappe, headers=headers_frappe, json=payload)
        
        return request_f
    except Exception as e:
        return f"Error get customer group: {e}"
    
@frappe.whitelist()
def get_customer_group_name(id):
    query = frappe.db.sql(f"""
                         SELECT customer_group_name FROM `tabCustomer Group` WHERE custom_customer_group_id = {id}
                         """, as_dict=True)
    customer_group = query[0]['customer_group_name']
    return customer_group

# @frappe.whitelist()
# def get_magento_product_details(sku):
#     try:
#         base_url, headers = base_request_magento_data()
#         url = f"{base_url}/rest/V1/products/{sku}"
#         request = requests.get(url, headers=headers)
#         request.raise_for_status() 

#         product_details = request.json()
        
#         item_code = product_details.get('sku')
#         item_name = product_details.get('name')
#         status = product_details.get('status')
#         custom_attributes = product_details.get('custom_attributes', [])

#         description = ""
#         image = None
#         category_id = None

#         for attribute in custom_attributes:
#             if attribute['attribute_code'] == 'short_description':
#                 description = attribute['value']
#             if attribute['attribute_code'] == 'category_ids':
#                 category_id = int(attribute['value'][0])
#             if attribute['attribute_code'] == 'image':
#                 image = attribute['value']
        
#         item_group = get_magento_categories(category_id)['name'] if category_id else ""

#         return {
#             "item_code": item_code,
#             "item_name": item_name,
#             "status": status,
#             "item_group": item_group,
#             "description": description,
#             "image": image
#         }
#     except Exception as e:
#         frappe.throw(f"Error fetching product details from Magento: {e}", "Magento Product Sync")
#         return {}

# @frappe.whitelist()
# def get_magento_customer_details(order_id):
#     try:
#         base_url, headers = base_request_magento_data()
#         url = f"{base_url}/rest/V1/orders/{order_id}"
#         request = requests.get(url, headers=headers)
#         request.raise_for_status()  

#         order_details = request.json()
        
#         customer_first_name = order_details['billing_address'].get('firstname', '')
#         customer_last_name = order_details['billing_address'].get('lastname', '')
#         customer_email = order_details['billing_address'].get('email', '')
#         customer_group_id = order_details.get('customer_group_id')
#         customer_group_name = get_customer_group_name(customer_group_id)

#         full_name = f"{customer_first_name} {customer_last_name}"
        
#         return {
#             "customer_name": full_name,
#             "custom_first_name": customer_first_name,
#             "custom_last_name": customer_last_name,
#             "custom_email": customer_email,
#             "customer_group": customer_group_name,
#             "custom_customer_group_id": customer_group_id
#         }
#     except Exception as e:
#         frappe.throw(f"Error fetching customer details from Magento: {e}", "Magento Customer Sync")
#         return {}

@frappe.whitelist()
def get_magento_sales_invoices(customer_id, sku):
    try:
        base_url, headers = base_request_magento_data()
        url = f"{base_url}/rest/V1/invoices?searchCriteria"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        json_response = response.json()

        base_url_frappe_sales_invoice, headers_frappe_sales_invoice = base_request_data()

        if "items" in json_response and json_response["items"]:
            magento_invoice = json_response["items"][0]
            customer_id = magento_invoice.get("customer_id")

            customer_details = customer_id
            customer_name = customer_details.get("customer_name", "Unknown Customer")

            data = {
                "customer": customer_name,
                "posting_date": magento_invoice["created_at"],
                "grand_total": magento_invoice["grand_total"],
                "items": []
            }

            for item in magento_invoice["items"]:
                sku = item["sku"]
                
                product_details = sku
                
                if product_details:
                    image_url = product_details.get("image")
                    image = upload_image_to_frappe(image_url, product_details["item_code"]) if image_url else ''

                    data["items"].append({
                        "item_code": product_details["item_code"],
                        "item_name": product_details["item_name"],
                        "qty": item["qty"],
                        "rate": item["price"],
                        "amount": item["row_total"],
                        "description": product_details.get("description", ""),
                        "image": image
                    })

            frappe_response = requests.post(
                f"{base_url_frappe_sales_invoice}/api/resource/Sales Invoice", 
                headers=headers_frappe_sales_invoice, 
                json=data
            )
            frappe_response.raise_for_status()

            return _("Sales invoice created successfully in Frappe.")
        else:
            return _("No invoices found.")

    except requests.exceptions.RequestException as e:
        frappe.throw(_("Error connecting to Magento API: {0}").format(str(e)), "Magento Sync")
    except KeyError as e:
        frappe.throw(_("Missing expected data: {0}").format(str(e)), "Magento Sync")
    except Exception as e:
        frappe.throw(_("Error creating sales invoice: {0}").format(str(e)), "Magento Sync")

@frappe.whitelist()
def get_magento_sales_order():
    base_url, headers = base_request_magento_data()
    try:
        response = requests.get(f'{base_url}/rest/V1/orders?searchCriteria', headers=headers)
        json_response = response.json()
        sales_order = json_response['items']
        return sales_order
    except Exception as e:
        return f"Error Get Sales Order: {e}"
    
@frappe.whitelist()
def get_customer_address():
    magento_so = get_magento_sales_order()
    try:
        addresses = []
        for address in magento_so:
            billing_address = address['billing_address']
            addresses.append(billing_address)
                    
        return addresses
    except Exception as e:
        return f"Error Get Customer Address: {e}"

def get_country_name(country_code):
    response = requests.get(f'https://restcountries.com/v3.1/alpha/{country_code}')
    if response.status_code == 200:
        data = response.json()
        return data[0]['name']['common']
    return "Unknown Country"

@frappe.whitelist()
def create_customer_address():
    magento_addresses = get_customer_address()
    base_url, headers = base_request_data()
    try:
        results = []
        for address in magento_addresses:
            country_name = get_country_name(address['country_id'])
            address_type = address['address_type'].title()
            payload = {
                "doctype": "Address",
                "address_type": address_type,
                "address_line1": address['street'][0],
                "city": address['city'],
                "country": country_name,
                "pincode": address['postcode'],
                "phone": address['telephone'],
                "email_id": address['email'],
                "is_shipping_address": 1,
                "links": [
                    {
                        "link_doctype": "Customer",
                        "link_name": f"{address['firstname']} {address['lastname']}"
                    }
                ]
            }
            response = requests.post(f'{base_url}/Address', headers=headers, json=payload)
            if response.status_code == 200:
                results.append(f"Address created successfully: {response.json()}")
            else:
                results.append(f"Failed to create address: {response.json()}")

        return "Address created successfully"
    except Exception as e:
        return f"Error Create Customer Address: {e}"
    
@frappe.whitelist()
def create_sales_order():
    base_url, headers = base_request_magento_data()
    frappe_base_url, frappe_headers = base_request_data()
    
    try:
        sales_order = get_magento_sales_order()
        for order in sales_order:
            so_items = []
            customer = order['customer_firstname'] + ' ' + order['customer_lastname']
            transaction_date = order['created_at'].split('T')[0]
            sales_order_status = order['status']
            customer_address = order['billing_address_id']
            
            for item in order['items']:
                dict_items = {
                    'item_code': item['sku'],
                    'delivery_date': str(date.today()),
                    'qty': item['qty_ordered'],
                    'rate': item['price']
                }
                so_items.append(dict_items)
                
            payload = {
                'customer': customer,
                'transaction_date': transaction_date,
                "custom_sales_order_status": sales_order_status,
                'items': so_items
            }
            
            response = requests.post(f'{frappe_base_url}/Sales Order', headers=frappe_headers, json=payload)
            response.raise_for_status()
        
        return "Sales Orders created successfully"
    
    except Exception as e:
        return f"Error creating sales order: {e}"

@frappe.whitelist()
def create_magento_auth():
    base_url, headers = base_request_magento_data()
    username, password = magento_admin_details()
    url = f"{base_url}/rest/V1/integration/admin/token"
    payload = {
        "username": username,
        "password": password
    }
    
    response = requests.post(url, json=payload)
    auth = response.text.strip('"')
    setting = frappe.get_doc("Magento Setting")
    setting.magento_auth = auth
    setting.save()
    return auth