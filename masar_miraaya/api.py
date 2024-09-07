# from __future__ import unicode_literals
import frappe
import json
import requests
from urllib.parse import urlparse
from io import BytesIO
import base64
import pycountry
import time
from datetime import date

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
def create_brand(brand):
    base_url_frappe, headers_frappe = base_request_data()
    payload = {
        "doctype": "Brand",
        "brand": brand
    }
    existing_brand = frappe.db.exists('Brand', brand)
    if existing_brand:
        return
    response = requests.post(f"{base_url_frappe}/Brand", headers=headers_frappe, json=payload)
    response.raise_for_status()

#####################################################################################

# def get_magento_products():
#     try:
#         response_json = get_magento_products_json()
#         all_items = response_json['items']
#         batch_size = 50
#         item_count = 0
#         items_to_commit = []

#         for item in all_items:
#             category_id_max = 0 
#             item_id = item['id']
#             item_code = item['sku']
#             item_name = item['name']
#             existing_item = frappe.db.exists("Item", {"item_code": item_code})
#             if existing_item:
#                 continue

#             visibility_mapping = {
#                 1: 'Not Visible Individually',
#                 2: 'Catalog',
#                 3: 'Search',
#                 4: 'Catalog & Search'
#             }
#             visibility = visibility_mapping.get(item['visibility'], 'Unknown')

#             if item['extension_attributes'] and item['extension_attributes']['category_links']:
#                 category_links = item['extension_attributes']['category_links']
#                 for cat_id in category_links:
#                     category_id = int(cat_id['category_id'])
#                     if category_id_max == 0 or category_id > category_id_max:
#                         category_id_max = category_id
            
#             item_group = get_item_group_by_item_group_id(category_id_max) if category_id_max else None

#             if item['status'] == 1:
#                 publish_to_magento = 1 
#                 disabled = 0 
#             elif item['status'] == 2:
#                 publish_to_magento = 0
#                 disabled = 1 
#             new_item_ = frappe.new_doc('Item')
#             new_item_.item_code = item_code
#             new_item_.item_name = item_name
#             new_item_.custom_item_id = item_id
#             new_item_.item_group = item_group
#             new_item_.custom_visibility = visibility
#             new_item_.save()
#             frappe.db.set_value('Item' ,new_item_.name , 'custom_is_publish' , publish_to_magento )
#             frappe.db.set_value('Item' ,new_item_.name , 'disabled' , disabled )
#             try:
#                 for media in item['media_gallery_entries']:
#                         if media['media_type'] ==  "image":
#                             if len(media['types']) !=0 : 
#                                 base_image = 1 
#                             else:
#                                 base_image = 0 
#                             url_file  = upload_image_to_item(
#                                                     file=media['file'], 
#                                                     item_code= item_code,
#                                                     base_image = base_image
#                                                     )
#                             if url_file :
#                                 frappe.db.set_value('Item' ,new_item_.name , 'image' , url_file )

#             except Exception as ex:
#                 frappe.log_error(message=str(ex), title="Error while uploading images to item")
#                 continue

#             item_count += 1

#             if item_count % batch_size == 0:
#                 for item_to_commit in items_to_commit:
#                     item_to_commit.save()
                
#                 frappe.db.commit()
#                 items_to_commit.clear() 
#         if items_to_commit:
#             for item_to_commit in items_to_commit:
#                 item_to_commit.save()
#             frappe.db.commit()
            
#     except Exception as ex:
#         frappe.log_error(message=str(ex), title="Exception in process_magento_products")


# @frappe.whitelist()
# def enqueue_magento_products():
#     frappe.enqueue('masar_miraaya.api.get_magento_products', queue='long',timeout=None,is_async=True,enqueue_after_commit=True,at_front=True)
#     return "Job enqueued successfully!"
    
    
################################################################################       

# @frappe.whitelist()
# def get_magento_products_():
#     try:
#         base_url, headers = base_request_magento_data()
#         url = base_url + "/rest/V1/products?searchCriteria="
#         request = requests.get(url, headers=headers)
#         json_response = request.json()
#         items = json_response['items']
#         items_list = []
#         description = ''
#         item_group = ''

#         if items:
#             for item in items:
#                 item_code = item['sku']
#                 item_name = item['name']
#                 status = item['status']

#                 custom_attributes = item['custom_attributes']
#                 image = None  
#                 category_id = None 

#                 for attribute in custom_attributes:
#                     if attribute['attribute_code'] == 'product_description':
#                         description = attribute['value'] if attribute['value'] else ""
#                     if attribute['attribute_code'] == 'brand':
#                         brand = attribute['value'] if attribute['value'] else ""
#                     if attribute['attribute_code'] == 'category_ids':
#                         category_id = int(attribute['value'][0])
#                         item_group_data = get_magento_categories(category_id)
#                         item_group = item_group_data['name']
#                     if attribute['attribute_code'] == 'image':
#                         image = attribute['value']
                
#                 file_url = upload_image_to_frappe(image, item_code) if image else ''
#                 if brand:
#                     create_brand(brand)
                        
#                 dict_items = {
#                     "naming_series": "STO-ITEM-.YYYY.-",
#                     "doctype": "Item",
#                     "item_code": item_code,
#                     "item_name": item_name,
#                     "status": status,
#                     "item_group": f"{str(category_id)} - {item_group}",
#                     "custom_item_group_id": category_id,
#                     "description": description,
#                     "brand": brand,
#                     "image": file_url,
#                     "custom_is_publish": 1
#                 }
#                 frappe.enqueue("masar_miraaya.api.create_item_task", timeout=None, queue="long", item_data=dict_items)
#                 # base_url_frappe, headers_frappe = base_request_data()
#                 # response = requests.post(f"{base_url_frappe}/Item", headers=headers_frappe, json=dict_items)
#                 # response.raise_for_status() 

#                 items_list.append(dict_items)

#         return items_list
#     except Exception as e:
#         frappe.throw(f"General Error: {e}", "Magento Sync")
#         return f"General Error: {e}"
# @frappe.whitelist()
# def create_item_group_():
#     def process_category(category, parent_name, item_group_name_list):
#         category_name = category['name']
#         category_id = category['id']
#         parent_id = category['parent_id']
#         category_status = 1 if category['is_active'] else 0
#         unique_name = f"{category_id} - {category_name}"
        
#         existing_item_group = frappe.db.sql("SELECT name FROM `tabItem Group` WHERE name = %s " , (unique_name) , as_dict = True)
#         if  (existing_item_group and existing_item_group[0] and existing_item_group[0]['name']):
#             print("@@@@@@@@@@@@@@@@@@@@@@@@@")
#             pass
#         else:
#             payload = {
#                 "doctype": "Item Group",
#                 "item_group_name": unique_name,
#                 "parent_item_group": parent_name,
#                 "custom_item_group_id": category_id,
#                 "custom_parent_item_group_id": parent_id,
#                 "custom_is_publish": 0,
#                 "is_group": 1 if 'children_data' in category and category['children_data'] else 0
#             }
#             ############### Start Create Brand 
#             if "404" in parent_id:
#                 exist_barnd = frappe.db.sql("SELECT name FROM `tabBrand` WHERE name = %s " , category_name , as_dict=1 )
#                 if  not (exist_barnd and exist_barnd[0] and exist_barnd[0]['name']):
#                     if not (category_name == "Brands"):
#                         new_brand = frappe.new_doc('Brand')
#                         new_brand.brand = category_name
#                         new_brand.save(ignore_permissions = True )
#                         frappe.db.set_value('Brand' , new_brand.name , 'brand' ,category_name )
#                         frappe.db.commit()
#             ############### End Create Brand 
#             base_url, headers = base_request_data()

#             try:
#                 print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
#                 frappe.msgprint("JJJJJ" , alert= True)
#                 response = requests.post(f"{base_url}/Item Group", headers=headers, json=payload)
#                 response.raise_for_status()
#                 item_group_name_list.append(unique_name)
#             except requests.exceptions.RequestException as e:
#                 frappe.log_error(f"Failed to create Item Group: {unique_name}, Error: {str(e)}")
#                 return
#         if 'children_data' in category and category['children_data']:
#             for child in category['children_data']:
#                 process_category(child, unique_name, item_group_name_list)

#     def update_item_groups_publish_status(item_group_names, publish_status):
#         for name in item_group_names:
#             frappe.db.set_value("Item Group", {"item_group_name": name}, "custom_is_publish", publish_status)

#     try:
        
#         base_url, headers = base_request_data()
#         magento_categories = get_magento_categories()
#         item_group_name_list = []
#         root_category = magento_categories['name']
#         root_id = magento_categories['id']
#         root_parent_id = magento_categories['parent_id']
#         root_status = 1

#         root_unique_name = f"{root_id} - {root_category}"

#         existing_root_item_group = frappe.get_all("Item Group", filters={"item_group_name": root_unique_name, "parent_item_group": ""})
#         if not existing_root_item_group:
#             root_payload = {
#                 "doctype": "Item Group",
#                 "item_group_name": root_unique_name,
#                 "parent_item_group": "",
#                 "custom_item_group_id": root_id,
#                 "custom_parent_item_group_id": root_parent_id,
#                 "custom_is_publish": 0,
#                 "is_group": 1
#             }
            
#             try:
#                 response = requests.post(f"{base_url}/Item Group", headers=headers, json=root_payload)
#                 response.raise_for_status()
#                 item_group_name_list.append(root_unique_name)
#             except requests.exceptions.RequestException as e:
#                 frappe.log_error(f"Failed to create Root Item Group: {root_unique_name}, Error: {str(e)}")
#                 return

#         all_categories = magento_categories.get('children_data', [])
#         for category in all_categories:
#             print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
#             process_category(category, root_unique_name, item_group_name_list)

#         update_item_groups_publish_status(item_group_name_list, 1)

#         return "Item Groups created successfully"
#     except Exception as e:
#         return f"Create Item Group Error: {str(e)}"


@frappe.whitelist()  
def get_magento_customers():
    try:
        base_url, headers = base_request_magento_data()
        url = base_url + "/rest/V1/customers/search?searchCriteria="
        request = requests.get(url, headers=headers)
        json_response = request.json()
        customers = json_response['items']

        for customer in customers:
            customer_id = customer['id']
            customer_group_id = customer['group_id']
            customer_group_name = get_customer_group_name(customer_group_id)
            customer_first_name = customer.get('firstname', "")
            customer_middle_name = customer.get('middlename', "")
            customer_tax_id = customer.get('taxvat', "")
            # (customer['lastname'] not in [None, "", '', 0, ' ', " "])
            customer_last_name = customer.get('lastname', "")
            is_subscribed = 1 if customer['extension_attributes']['is_subscribed'] == 'true' else 0
            store_id = customer['store_id']
            website_id = customer['website_id']
            customer_dob = customer.get('dob', "")
            full_name = " ".join([customer_first_name, customer_last_name])
            customer_name = f"{customer_id} - {full_name}"
            customer_email = customer['email']
            customer_gender = customer.get('gender', "")
            customer_prefix = customer.get('prefix', "")
            customer_suffix = customer.get('suffix', "")
            
            if customer_gender == 1:
                customer_gender = "Male"
            elif customer_gender == 2:
                customer_gender = "Female"
            else:
                customer_gender = 0
                                
            existing_customers = frappe.db.sql(""" Select customer_name, custom_first_name, custom_last_name 
                                               FROM `tabCustomer` 
                                               WHERE customer_name = %s AND custom_customer_id = %s  """,
                                               (customer_name, customer_id), as_dict = True)
            if not (existing_customers and existing_customers[0] and existing_customers[0]['customer_name']):
                new_customer = frappe.new_doc('Customer')
                new_customer.custom_customer_id = customer_id
                new_customer.customer_name = customer_name
                new_customer.custom_first_name = customer_first_name
                new_customer.custom_middle_name = customer_middle_name
                new_customer.custom_last_name = customer_last_name if customer_last_name not in [None, "", '', 0, ' ', " "] else "Test"
                new_customer.custom_prefix = customer_prefix
                new_customer.custom_suffix = customer_suffix
                new_customer.custom_email = customer_email
                new_customer.customer_group = customer_group_name
                new_customer.gender = customer_gender
                new_customer.custom_customer_group_id = customer_group_id
                new_customer.custom_is_subscribed = is_subscribed
                new_customer.customer_type = 'Individual'
                new_customer.custom_is_publish = 1
                new_customer.disabled = 0
                new_customer.tax_id = customer_tax_id
                new_customer.tax_category = 'Retail Customer'
                new_customer.custom_website_id = website_id
                new_customer.custom_store_id = store_id
                new_customer.custom_date_of_birth = customer_dob
                new_customer.save(ignore_permissions = True)

            
            adresses = customer['addresses']
            for address in adresses:
                address_id = address['id']
                address_line = address['street'][0]
                country = address['region']['region']
                country_id = address['country_id']
                city = address['city']
                pincode = address['postcode']
                phone = address['telephone']
                email_id = customer_email
                customer_id_address = address['customer_id']
                first_name = address.get('firstname', "")
                # (customer['lastname'] not in [None, "", '', 0, ' ', " "])
                last_name = address.get('lastname', "")
                default_shipping = 1 if address.get('default_shipping', "") == 'true' else 0
                existing_address = frappe.db.sql(
                    """SELECT name FROM `tabAddress`
                    WHERE address_line1 = %s AND city = %s AND pincode = %s AND phone = %s AND email_id = %s""",
                    (address_line, city, pincode, phone, email_id),
                    as_dict=True
                )
                if not (existing_address and existing_address[0] and existing_address[0]['name']):
                    new_address = frappe.new_doc("Address")
                    new_address.custom_address_id = address_id
                    new_address.custom_customer_id = customer_id_address
                    new_address.address_line1 = address_line
                    new_address.country = country
                    new_address.custom_country_id = country_id
                    new_address.city = city
                    new_address.pincode = pincode
                    new_address.phone = phone
                    new_address.custom_first_name = first_name
                    new_address.custom_last_name = last_name if last_name not in [None, "", '', 0, ' ', " "] else "Test"
                    new_address.email_id = email_id
                    new_address.is_shipping_address = 1 #default_shipping
                    new_address.is_primary_address = 1
                    new_address.tax_category = 'Retail Customer'
                    new_address.append('links', {
                            'link_doctype': "Customer",
                            'link_name': customer_name
                        })
                    new_address.save(ignore_permissions = True)
                
        return "Customers Created Successfully"
    except Exception as e:
        return f"Error get customers: {e}"
    
@frappe.whitelist()
def get_customer_group():
    try:
        base_url, headers = base_request_magento_data()
        base_url_frappe, headers_frappe = base_request_data()
        
        existing_customer_group = frappe.db.sql("Select name FROM `tabCustomer Group` WHERE name = 'All Customer Groups'", as_dict = True)
        if not (existing_customer_group and existing_customer_group[0] and existing_customer_group[0]['name']):
            new_customer_group = frappe.new_doc('Customer Group')
            new_customer_group.customer_group_name = "All Customer Groups"
            new_customer_group.is_group = 1
            new_customer_group.custom_customer_group_id = 99999
            new_customer_group.save(ignore_permissions=True)
            
        url = base_url + "/rest/V1/customerGroups/search?searchCriteria="
        request = requests.get(url, headers=headers)
        json_response = request.json()
        customer_groups = json_response['items']
        
        for group in customer_groups:
            customer_group_id = group['id']
            customer_group_name = group['code']
            tax_class_id = group['tax_class_id']
            tax_class_name = group['tax_class_name']
            
            existing_customer_group = frappe.db.sql("Select name FROM `tabCustomer Group` WHERE name = %s",(customer_group_name), as_dict = True)
            if not (existing_customer_group and existing_customer_group[0] and existing_customer_group[0]['name']):
                new_group = frappe.new_doc('Customer Group')
                new_group.customer_group_name = customer_group_name
                new_group.custom_customer_group_id = customer_group_id
                new_group.parent_customer_group = "All Customer Groups"
                new_group.save(ignore_permissions=True)
            
            existing_tax_group = frappe.db.sql("Select name FROM `tabTax Category` WHERE name = %s", (tax_class_name), as_dict = True)
            if not (existing_tax_group and existing_tax_group[0] and existing_tax_group[0]['name']):
                new_tax_group = frappe.new_doc('Tax Category')
                new_tax_group.title = tax_class_name
                new_tax_group.custom_tax_category_id = tax_class_id
                new_tax_group.save(ignore_permissions=True)
                
        return "Customer groups synchronized successfully"
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
def get_magento_sales_invoices():
    try:
        base_url, headers = base_request_magento_data()
        url = base_url + "/rest/V1/invoices?searchCriteria"
        request = requests.get(url, headers=headers)
        json_response = request.json()

        base_url_frappe_sales_invoice, headers_frappe_sales_invoice = base_request_data()

        if "items" in json_response and len(json_response["items"]) > 0:
            for magento_invoice in json_response["items"]:
                customer_id = magento_invoice.get("customer_id")

                customer_details = requests.get(f"{base_url_frappe_sales_invoice}/Customer", headers=headers_frappe_sales_invoice, params={"custom_customer_id": customer_id}).json()
                customer_name = customer_details.get("customer_name", "Unknown Customer") if customer_details else "Unknown Customer"

                data = {
                    "customer": customer_name,
                    "posting_date": magento_invoice["created_at"],
                    "grand_total": magento_invoice["grand_total"],
                    "items": []
                }

                if isinstance(magento_invoice["items"], list):
                    for item in magento_invoice["items"]:
                        sku = item["sku"]

                        product_details = requests.get(f"{base_url_frappe_sales_invoice}/Item", headers=headers_frappe_sales_invoice, params={"item_code": sku}).json()

                        if product_details:
                            data["items"].append({
                                "item_code": product_details["item_code"],
                                "item_name": product_details["item_name"],
                                "qty": item["qty"],
                                "rate": item["price"],
                                "amount": item["row_total"],
                                "description": product_details["description"],
                                "image": product_details["image"]
                            })

                response = requests.post(f"{base_url_frappe_sales_invoice}/Sales Invoice", headers=headers_frappe_sales_invoice, json=data)
                response.raise_for_status()

        return "Sales invoices created successfully."
    except Exception as e:
        frappe.throw(f"Error creating sales invoices: {e}", "Magento Sync")
        return f"Error creating sales invoices: {e}"

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
    
    query = frappe.db.sql("SELECT name FROM `tabWebhook Header` WHERE `key` = 'Authorization'", as_dict=True)
    webhook_auth = f"Bearer {auth}"
    
    for header in query:
        frappe.db.set_value("Webhook Header", header['name'], 'value', webhook_auth)
    frappe.db.commit()
    return auth




# ##########################################################################
# def base_request_magento_data():
#     setting = frappe.get_doc("Magento Setting")
#     base_url = str(setting.magento_url).strip()
#     headers = {
#         "Authorization": f"Bearer {str(setting.magento_auth).strip()}",
#         "Content-Type": "application/json"
#     }
#     return base_url , headers

# @frappe.whitelist()
# def get_magento_item_attribute(all_items , all_configurable , altenative_items):
#     try:
#         frappe.enqueue(
#             'masar_miraaya.api.get_magento_item_attributes_in_enqueue',
#             queue='long',
#             timeout=5000,
#             is_async=True,
#             enqueue_after_commit=True,
#             at_front=True,
#             all_items = all_items , 
#             all_configurable = all_configurable , 
#             altenative_items = altenative_items
#         )
#     except Exception as ex:
#         return f"Error While Sync with Brand {str(ex)}"

# def get_magento_item_attributes_in_enqueue(all_items , all_configurable , altenative_items):
#     base_url, headers = base_request_magento_data()
#     try:
#         url = base_url + "/rest/V1/products/attributes?searchCriteria[pageSize]=100"
#         response = requests.get(url, headers=headers)
#         response.raise_for_status()
#         json_response = response.json()
#         attributes = [attr for attr in json_response['items'] if attr['attribute_code'] in ['color', 'size_ml', 'shade', 'size']]
#         for attribute in attributes:
#             process_item_attribute(attribute['default_frontend_label'], attribute['options'],attribute['attribute_code'] ) 
#         # return "Success"
#     except requests.exceptions.RequestException as e:
#         return f"Error getting Magento colors: {e}"
#     except Exception as e:
#         return f"Error processing Magento colors: {e}"
#     try:
#         frappe.enqueue(
#             'masar_miraaya.api.create_templete_items',
#             queue='long',
#             timeout=5000,
#             is_async=True,
#             enqueue_after_commit=True,
#             at_front=True,
#             all_items=all_items ,
#             all_configurable = all_configurable,
#             altenative_items = altenative_items
#         )
#     except Exception as ex:
#         return f"Error while Create Item Templete {str(ex)}"
    

# def process_item_attribute(default_frontend_label, options , attribute_code):
#     try:
#         if frappe.db.exists('Item Attribute', default_frontend_label):
#             item_attribute = frappe.get_doc('Item Attribute', default_frontend_label)
#         else:
#             item_attribute = frappe.new_doc('Item Attribute')
#             item_attribute.attribute_name = default_frontend_label
#             item_attribute.custom_attribute_code = attribute_code
#             item_attribute.insert(ignore_permissions=True)
        
#         for option in options:
#             if (option['value'] not in [None, "", '', 0, ' ', " "]) and (option['label'] not in [None, "", '', 0, " ", ' ']):
#                 existing_attribute_value = frappe.db.get_value('Item Attribute Value', {
#                     'parent': default_frontend_label,
#                     'attribute_value': str(option['label'])
#                 }, 'name')
#                 if not existing_attribute_value:
#                     new_attribute_value = frappe.new_doc('Item Attribute Value')
#                     new_attribute_value.attribute_value = str(option['label'])
#                     new_attribute_value.abbr = str(option['value'])
#                     new_attribute_value.parent = default_frontend_label
#                     new_attribute_value.parentfield = 'item_attribute_values'
#                     new_attribute_value.parenttype = 'Item Attribute'
#                     new_attribute_value.insert(ignore_permissions=True)
#     except frappe.DatabaseError as e:
#         return f"Error processing attribute {default_frontend_label}: {e}"
#     except Exception as e:
#         return f"Error processing attribute {default_frontend_label}: {e}"

    
# ################### From Mahmoud 
# ############# To Sync with Item Group 
# @frappe.whitelist()
# def get_magento_categories(id=None):
#     try:
#         base_url, headers = base_request_magento_data()
#         if id:
#             url = base_url + f"/rest/V1/categories/{id}"
#         else:
#             url = f"{base_url}/rest/all/V1/categories"
#         request = requests.get(url, headers=headers)
#         return request.json()
#     except Exception as e:
#         return f"Get Magento Categories Error: {e}"
# @frappe.whitelist()
# def create_item_group():
#     try:
#         magento_categories = get_magento_categories()
#         existing_root_item_group = frappe.db.sql("SELECT name FROM `tabItem Group` WHERE custom_parent_item_group_id = 0 " , as_dict=True)
#         if not(existing_root_item_group and existing_root_item_group[0] and existing_root_item_group[0]['name']):
#             root_category = magento_categories['name']
#             root_id = magento_categories['id']
#             root_parent_id = magento_categories['parent_id']
#             root_status = 1
#             root_unique_name = f"{root_id} - {root_category}"
#             new_root = frappe.new_doc('Item Group')
#             new_root.item_group_name = root_unique_name
#             new_root.parent_item_group = None
#             new_root.custom_item_group_id = root_id
#             new_root.custom_parent_item_group_id = root_parent_id
#             new_root.is_group = 1
#             new_root.save(ignore_permissions = True)
#             frappe.db.set_value("Item Group" ,new_root.name , 'custom_is_publish' , root_status )
#             frappe.db.commit()
#         else: 
#             root_unique_name = existing_root_item_group[0]['name']
#         if len(magento_categories['children_data']) !=0:
#             create_item_group_childs_loop(root_unique_name  , magento_categories['children_data'])
#             return "Sync Item Group Successfully"
#     except Exception as e:
#         return f"Create Item Group Error: {str(e)}"

# def create_item_group_childs_loop(parent , children_data_list):
#     for children_data in children_data_list:
#         create_item_group_childs(parent , children_data)

# def create_item_group_childs(parent , children_data): 
#         category_name = children_data['name']
#         category_id = children_data['id']
#         parent_id = children_data['parent_id']
#         category_status = 1 if children_data['is_active'] else 0
#         if len(children_data['children_data']) !=0:
#             is_group = 1 
#         else : 
#             is_group = 0 
#         unique_name = f"{category_id} - {category_name}"
#         existing_item_group = frappe.db.sql("SELECT name , parent_item_group FROM `tabItem Group` WHERE name = %s " , (unique_name) , as_dict = True)
#         if existing_item_group and existing_item_group[0]:
#             if existing_item_group[0]['parent_item_group'] != parent:
#                 update_parent = frappe.get_doc('Item Group' ,existing_item_group[0]['name'] )
#                 update_parent.parent_item_group = parent
#                 update_parent.save(ignore_permissions = True)
#                 frappe.db.set_value("Item Group" ,existing_item_group[0]['name'] , 'parent_item_group' , parent )
#                 frappe.db.commit()
#         else:
#             new_root = frappe.new_doc('Item Group')
#             new_root.item_group_name = unique_name
#             new_root.parent_item_group = parent
#             new_root.custom_item_group_id = category_id
#             new_root.custom_parent_item_group_id = parent_id
#             new_root.is_group = is_group
#             new_root.save(ignore_permissions = True)
#             frappe.db.set_value("Item Group" ,new_root.name , 'custom_is_publish' , category_status )
#             frappe.db.commit() 
#         if  is_group:
#              create_item_group_childs_loop(unique_name , children_data['children_data'])
# ###################### Check Item Group 
# @frappe.whitelist()
# def get_item_group_by_item_group_id(category_id):
#     try:
#         item_group_sql = frappe.db.sql("""
#             SELECT name 
#             FROM `tabItem Group` 
#             WHERE custom_item_group_id = %s
#         """, (str(category_id)), as_dict=True)
#         if item_group_sql and item_group_sql[0] and item_group_sql[0]['name']:
#             return item_group_sql[0]['name']
#         else:
#             create_item_group()
#             item_group_sql = frappe.db.sql("""
#                 SELECT name 
#                 FROM `tabItem Group` 
#                 WHERE custom_item_group_id = %s
#             """, (str(category_id)), as_dict=True)
#             return item_group_sql[0]['name'] if item_group_sql and item_group_sql[0] else None     
#     except Exception as ex:
#         return (f"Error in get_item_group_by_item_group_id: {str(ex)}")
# ######################################################################### 
# ############### To Sync to Brand 
# @frappe.whitelist()
# def get_magento_brand(response_json):
#     try:
#         create_item_group()
#     except Exception as ex : 
#         return "Exception Sync Item Group from Brands :" + str(ex) 
#     try:
#         base_url_frappe, headers_frappe = base_request_data()
#         brands = frappe.db.sql("""SELECT item_group_name FROM `tabItem Group` tig WHERE custom_parent_item_group_id = '404' """, as_dict = True)
#         for brand in brands:
            
#             brand_name = brand['item_group_name'].split(' - ', 1)[-1].strip()
#             exist_brands = frappe.db.sql("""SELECT name FROM `tabBrand` WHERE name = %s""" , (brand_name) , as_dict = 1 )
#             if not (exist_brands and exist_brands[0] and exist_brands[0]['name']): 
#                 payload = {
#                     "doctype": "Brand",
#                     "brand": brand_name
#                 }
#                 response = requests.post(f"{base_url_frappe}/Brand", headers=headers_frappe, json=payload)
#                 response.raise_for_status()
#         # return "Sync Brand and Item Group Completed Successfully"
#     except Exception as e:
#         return (f"General Error: {e}", "Magento Sync")
    
#     all_items = response_json['items']
#     all_configurable = list()
#     altenative_items = list()
#     for configurable in all_items:
#         if configurable['type_id'] == "configurable":
#             templete_code = configurable['sku']
#             templete_id = configurable['id']
#             links_product = configurable['extension_attributes']['configurable_product_links']
#             all_configurable.append(frappe._dict(
#                         {
#                         'templete_code' : templete_code, 
#                         'templete_id' : templete_id,
#                         'links_product' : links_product
#                         }
#                     )
#                 )
#         if len(configurable["product_links"]) !=0:
#             altenative_items.append(frappe._dict({'links_product' : configurable["product_links"], }))
#     try:
#         get_magento_item_attribute_(all_items , all_configurable ,altenative_items )
#     except Exception as ex:
#         return f"Error while Sync in Item Attribute : {str(ex)}"
    
# def get_magento_item_attribute_(all_items , all_configurable ,altenative_items ):
#         get_magento_item_attribute(all_items , all_configurable ,altenative_items )


# ############################################################################
# ############ To Add Item images 
# @frappe.whitelist()
# def upload_image_to_item( file ,  item_code , base_image):
#     try:
#         image_url = validate_url(file)
#         response = requests.get(image_url)
#         response.raise_for_status()

#         image_content = BytesIO(response.content).getvalue()
#         image_base64 = base64.b64encode(image_content).decode('utf-8')

#         file_name = f"{file}"

#         _file = frappe.get_doc({
#             "doctype": "File",
#             "file_name": file_name,
#             "attached_to_doctype": "Item",
#             "attached_to_name": item_code,
#             "is_private": 0,
#             "content": image_base64,
#             "decode": True
#         })
#         _file.save()
#         if base_image:
#             return _file.file_url
#         else : 
#             return 0 
#     except Exception as e:
#         frappe.log_error(f"Upload Image Error for item {item_code}: {e}", "Image Upload")
#         return f"Upload Image Error: {e}"      

# ##################################################
# ###################### To Sync with item 
# @frappe.whitelist()
# def get_magento_products_json():
#         base_url, headers = base_request_magento_data()
#         url = base_url + "/rest/V1/products?searchCriteria="
#         request = requests.get(url, headers=headers)
#         json_response = request.json()
#         return json_response

# @frappe.whitelist()
# def get_magento_products():
#     try: 
#         response_json = get_magento_products_json()
#     except Exception as ex:
#         return f"Error in Magento Connection : {str(ex)}"
#     ####### Chech for Brand And Item Group 
#     try:
#         frappe.enqueue(
#             'masar_miraaya.api.get_magento_brand',
#             queue='long',
#             timeout=5000,
#             is_async=True,
#             enqueue_after_commit=True,
#             at_front=True,
#             response_json =response_json
#         )
#     except Exception as ex:
#         return f"Error While Sync with Brand {str(ex)}"
    

#      ### get varint items to build templete 
# def create_templete_items(all_items , all_configurable , altenative_items):
#     for configurable in all_items:
#         if configurable['type_id'] == "configurable":
#             category_id_max = 0 
#             exist_templete = frappe.db.sql("SELECT name FROM `tabItem` WHERE item_code = %s" ,(configurable['sku']) , as_dict=True)
#             if not(exist_templete and exist_templete[0] and exist_templete[0]['name']):
#                 templete_code = configurable['sku']
#                 templete_id = configurable['id']
#                 templete_name = configurable['name']
#                 if configurable['status'] == 1:
#                     publish_to_magento = 1 
#                     disabled = 0 
#                 elif configurable['status'] == 2:
#                     publish_to_magento = 0
#                     disabled = 1 
#                 visibility_mapping = {
#                         1: 'Not Visible Individually',
#                         2: 'Catalog',
#                         3: 'Search',
#                         4: 'Catalog & Search'
#                     }
#                 visibility = visibility_mapping.get(configurable['visibility'], '')
#                 if configurable['extension_attributes'] and configurable['extension_attributes']['category_links']:
#                     category_links = configurable['extension_attributes']['category_links']
#                     for cat_id in category_links:
#                             category_id = int(cat_id['category_id'])
#                             if category_id_max == 0 or category_id > category_id_max:
#                                     category_id_max = category_id
#                 if  category_id_max :
#                         item_group = get_item_group_by_item_group_id(category_id_max)
#                 has_variants = 1 
#                 ############# Create a Templete 
#                 new_templete = frappe.new_doc('Item')
#                 new_templete.item_code = templete_code
#                 new_templete.item_name = templete_name
#                 new_templete.custom_item_id = templete_id
#                 new_templete.item_group = item_group
#                 new_templete.custom_visibility = visibility
#                 new_templete.insert(ignore_permissions=True)
#                 frappe.db.set_value('Item' ,new_templete.name , 'has_variants' , has_variants )
#                 new_templete.custom_magento_item_type = "configurable"
#                 configurable_options  = configurable['extension_attributes']['configurable_product_options']
#                 if len(configurable_options) !=0 :
#                     for options in configurable_options:
#                         attributes = frappe.new_doc("Item Variant Attribute")
#                         attributes.attribute =  str(options['label'])
#                         attributes.parentfield = 'attributes'
#                         attributes.parenttype = 'Item'
#                         attributes.parent = new_templete.name
#                         attributes.insert(ignore_permissions=True)
#                 frappe.db.set_value('Item' ,new_templete.name , 'custom_is_publish' , publish_to_magento )
#                 frappe.db.set_value('Item' ,new_templete.name , 'disabled' , disabled )
#                 for custom_attributes in configurable['custom_attributes']:
#                     att_code =custom_attributes['attribute_code']
#                     att_value = custom_attributes['value']
#                     if att_code == "brand":
#                         brand_sql = frappe.db.sql("SELECT name FROM `tabBrand` WHERE name = %s" , (att_value) , as_dict = True)
#                         if brand_sql and brand_sql[0] and brand_sql[0]['name']:
#                             brand = brand_sql[0]['name']
#                         else:
#                             new_brand = frappe.new_doc('Brand')
#                             new_brand.brand = att_value
#                             new_brand.insert(ignore_permissions=True)
#                             brand = new_brand.name
#                         new_templete.brand = brand
#                         frappe.db.set_value('Item' ,new_templete.name , 'brand' , brand )
#                     if att_code == "free_from":
#                         if att_value not in [ None , ""]:
#                             frappe.db.set_value('Item' ,new_templete.name , 'custom_free_from' , att_value )
#                     if att_code == "key_features":
#                         if att_value not in [ None , ""]:
#                             frappe.db.set_value('Item' ,new_templete.name , 'custom_key_features' , att_value )
#                     if att_code == "ingredients":
#                         if att_value not in [ None , ""]:
#                             frappe.db.set_value('Item' ,new_templete.name , 'custom_ingredients' , att_value )
#                     if att_code == "how_to_use":
#                         if att_value not in [ None , ""]:
#                             frappe.db.set_value('Item' ,new_templete.name , 'custom_how_to_use' , att_value )
#                     if att_code == "formulation":
#                         if att_value not in [ None , ""]:
#                             frappe.db.set_value('Item' ,new_templete.name , 'custom_formulation' , att_value )
#                     if att_code == "product_description":
#                         if att_value not in [ None , ""]:
#                             frappe.db.set_value('Item' ,new_templete.name , 'description' , att_value )
#                     if att_code == "country_of_manufacture":
#                         if att_value not in [ None , ""]:
#                             frappe.db.set_value('Item' ,new_templete.name , 'custom_country_of_manufacture' , att_value )
#                 try:
#                         for media in configurable['media_gallery_entries']:
#                             if media['media_type'] ==  "image":
#                                 if len(media['types']) !=0 : 
#                                     base_image = 1 
#                                 else:
#                                     base_image = 0 
#                                 url_file  = upload_image_to_item(
#                                                         file=media['file'], 
#                                                         item_code= templete_code,
#                                                         base_image = base_image
#                                                         )
#                                 if url_file :
#                                     frappe.db.set_value('Item' ,new_templete.name , 'image' , url_file )
#                 except Exception as ex:
#                         return f"Error While upload Images to item "+ str(ex)
#     get_magento_products_in_enqueue_(all_items,all_configurable ,altenative_items)


# def get_magento_products_in_enqueue_(all_items ,all_configurable  ,altenative_items):
#     batch_size = 100
#     total_items = len(all_items)
#     final_loop = False
#     for i in range(0, len(all_items), batch_size):
#         if i + batch_size >= total_items:
#             final_loop = True
#         batch = all_items[i:i + batch_size]
#         frappe.enqueue(
#             'masar_miraaya.api.get_magento_products_in_enqueue',
#             queue='long',
#             timeout=5000,
#             is_async=True,
#             enqueue_after_commit=True,
#             at_front=True,
#             response_json={'items': batch} , 
#             all_configurable= all_configurable , 
#             final_loop = final_loop ,
#             altenative_items = altenative_items
#         )
    


#     return f"Done"


# def get_magento_products_in_enqueue(response_json, all_configurable, final_loop, altenative_items):
#     try:
#         all_items = response_json['items']
#         for item in all_items:
#             if item['type_id'] == "simple":
#                 # Initialize necessary variables and fetch existing item details
#                 category_id_max = 0 
#                 item_id = item['id']
#                 item_code = item['sku']
#                 item_name = item['name']
#                 rate = item['price']
#                 exist_item_code = frappe.db.sql("SELECT name FROM `tabItem` WHERE item_code = %s", (item_code,), as_dict=True)

#                 if not (exist_item_code and exist_item_code[0] and exist_item_code[0]['name']):
#                     visibility_mapping = {
#                         1: 'Not Visible Individually',
#                         2: 'Catalog',
#                         3: 'Search',
#                         4: 'Catalog & Search'
#                     }
#                     visibility = visibility_mapping.get(item['visibility'], '')
                    
#                     # Category processing
#                     if item['extension_attributes'] and item['extension_attributes']['category_links']:
#                         category_links = item['extension_attributes']['category_links']
#                         for cat_id in category_links:
#                             category_id = int(cat_id['category_id'])
#                             if category_id_max == 0 or category_id > category_id_max:
#                                 category_id_max = category_id
#                     if category_id_max:
#                         item_group = get_item_group_by_item_group_id(category_id_max)
                    
#                     # Status processing
#                     if item['status'] == 1:
#                         publish_to_magento = 1 
#                         disabled = 0 
#                     elif item['status'] == 2:
#                         publish_to_magento = 0
#                         disabled = 1 
                    
#                     # Create new Item document
#                     new_item_ = frappe.new_doc('Item')
#                     new_item_.item_code = item_code
#                     new_item_.item_name = item_name
#                     new_item_.custom_item_id = item_id
#                     new_item_.item_group = item_group
#                     new_item_.custom_visibility = visibility
#                     new_item_.custom_magento_item_type = "simple"
#                     new_item_.insert(ignore_permissions=True)
#                     # insert_item_price(
#                     #         item_code=new_item_.name ,
#                     #         uom = new_item_.stock_uom , 
#                     #         item_name=item_name ,
#                     #         brand = brand,
#                     #         rate = str(rate)
#                     #     )
#                     # Set additional values
#                     frappe.db.set_value('Item', new_item_.name, 'custom_is_publish', publish_to_magento)
#                     frappe.db.set_value('Item', new_item_.name, 'disabled', disabled)
                    
#                     # Variant processing
#                     for configurable in all_configurable:
#                         link_product = configurable['links_product']
#                         if item_id in link_product:
#                             variant_item_sql = frappe.db.sql("SELECT name FROM tabItem WHERE item_code = %s", (configurable['templete_code'],), as_dict=True)
#                             if variant_item_sql and variant_item_sql[0] and variant_item_sql[0]['name']:
#                                 frappe.db.set_value('Item', new_item_.name, 'variant_of', variant_item_sql[0]['name'])
                    
#                     # Custom attributes processing
#                     for custom_attributes in item['custom_attributes']:
#                         att_code = custom_attributes['attribute_code']
#                         att_value = custom_attributes['value']
#                         if att_code == "brand":
#                             brand_sql = frappe.db.sql("SELECT name FROM `tabBrand` WHERE name = %s", (att_value,), as_dict=True)
#                             if brand_sql and brand_sql[0] and brand_sql[0]['name']:
#                                 brand = brand_sql[0]['name']
#                             else:
#                                 new_brand = frappe.new_doc('Brand')
#                                 new_brand.brand = att_value
#                                 new_brand.insert(ignore_permissions=True)
#                                 brand = new_brand.name
#                             new_item_.brand = brand
#                         if att_code == "free_from" and att_value:
#                             frappe.db.set_value('Item', new_item_.name, 'custom_free_from', att_value)
#                         if att_code == "key_features" and att_value:
#                             frappe.db.set_value('Item', new_item_.name, 'custom_key_features', att_value)
#                         if att_code == "ingredients" and att_value:
#                             frappe.db.set_value('Item', new_item_.name, 'custom_ingredients', att_value)
#                         if att_code == "how_to_use" and att_value:
#                             frappe.db.set_value('Item', new_item_.name, 'custom_how_to_use', att_value)
#                         if att_code == "formulation" and att_value:
#                             frappe.db.set_value('Item', new_item_.name, 'custom_formulation', att_value)
#                         if att_code == "product_description" and att_value:
#                             frappe.db.set_value('Item', new_item_.name, 'description', att_value)
#                         if att_code == "country_of_manufacture" and att_value:
#                             frappe.db.set_value('Item', new_item_.name, 'custom_country_of_manufacture', att_value)

#                         #Handling item attributes for variants
#                         if att_code in ['color', 'size_ml', 'shade', 'size']:
#                             attribute_value = frappe.db.sql("""
#                             SELECT tia.name , tav.attribute_value FROM `tabItem Attribute` tia 
#                                         INNER JOIN  `tabItem Attribute Value` tav ON tia.name = tav.parent 
#                                         WHERE tav.abbr = %s OR tav.attribute_value =  %s
#                                         """, (str(att_value),str(att_value)), as_dict=True)
#                             if attribute_value and attribute_value[0] and attribute_value[0]['attribute_value']:
#                                 variant = attribute_value[0]['attribute_value']
#                             else:
#                                 variant = att_value
#                             if att_code == 'color':
#                                 frappe.db.set_value('Item', new_item_.name, 'custom_color', variant)
#                             if att_code == 'size':
#                                 frappe.db.set_value('Item', new_item_.name, 'custom_size', variant)

#                             if att_code == 'shade':
#                                 frappe.db.set_value('Item', new_item_.name, 'custom_shade', variant)

#                             if att_code == 'size_ml':
#                                 frappe.db.set_value('Item', new_item_.name, 'custom_size_ml', variant)

#                                 # item_attribute_sql = frappe.db.sql("SELECT custom_attribute_code FROM `tabItem Attribute`", as_dict=True)
#                                 # for item_attribute in item_attribute_sql:
#                                 #     if att_code == item_attribute.custom_attribute_code:
#                                 #         attribute_value = frappe.db.sql("""
#                                 #             SELECT tia.name , tav.attribute_value FROM `tabItem Attribute` tia 
#                                 #             INNER JOIN  `tabItem Attribute Value` tav ON tia.name = tav.parent 
#                                 #             WHERE tav.abbr = %s OR tav.attribute_value =  %s
#                                 #         """, (str(att_value),str(att_value)), as_dict=True)
#                                 #         # if attribute_value:
#                                 #         frappe.db.set_value('Item Variant Attribute', None, {
#                                 #                 'attribute': str(attribute_value[0]['name']),
#                                 #                 'attribute_value': str(attribute_value[0]['attribute_value']),
#                                 #                 'parent': new_item_.name,
#                                 #                 'parentfield': 'attributes',
#                                 #                 'parenttype': 'Item'
#                                 #             }, ignore_permissions=True, ignore_mandatory=True)
#                                 #             # Ensure data is committed to DB
#                     # frappe.db.commit()

#                     # Process images
#                     try:

#                         for media in item['media_gallery_entries']:
#                             if media['media_type'] == "image":
#                                 base_image = 1 if media['types'] else 0
#                                 url_file = upload_image_to_item(
#                                     file=media['file'], 
#                                     item_code=item_code,
#                                     base_image=base_image
#                                 )
#                                 if url_file:
#                                     frappe.db.set_value('Item', new_item_.name, 'image', url_file)
#                     except Exception as ex:
#                         return f"Error While uploading Images to item: {str(ex)}"
                        
#                     frappe.db.commit()  # Ensure all operations are committed

#         if final_loop and altenative_items:
#             frappe.enqueue(
#                 'masar_miraaya.api.get_alternative_items',
#                 queue='long',
#                 timeout=5000,
#                 is_async=True,
#                 enqueue_after_commit=True,
#                 at_front=True,
#                 altenative_items=altenative_items
#             )

#     except Exception as ex:
#         return f"Exception in get_magento_products: {str(ex)}"
# ############################## Inset Item Price 
# def insert_item_price(
#         item_code ,
#         item_name ,
#         brand,
#         uom , 
#         rate 
#     ):
#     price_list_sql = frappe.db.sql("SELECT name FROM `tabPrice List` tpl WHERE selling =1 AND custom_magento_selling =1 " , as_dict = True)
#     if price_list_sql and price_list_sql[0] and price_list_sql[0]['name']:
#         price_list = price_list_sql[0]['name']
#     else: 
#         price_list_sql_selling = frappe.db.sql("SELECT name FROM `tabPrice List` tpl WHERE selling =1" , as_dict = True)
#         price_list = price_list_sql_selling[0]['name']
#     item_price = frappe.new_doc('Item Price')
#     item_price.item_code = item_code
#     item_price.item_name = item_name
#     item_price.price_list = price_list
#     item_price.uom = uom
#     item_price.brand = brand
#     item_price.rate =float(rate)
#     item_price.insert(ignore_permissions=True , ignore_mandatory=True)
# ####################################### Insert Item Alternative 
# def get_alternative_items(altenative_items):
#     for altenative in altenative_items: 
#         for links in altenative['links_product']:
#             if links["link_type"] == "related": 
#                 frappe.db.set_value('Item' , links['sku'] , 'allow_alternative_item' , 1 )
#                 frappe.db.set_value('Item' , links['linked_product_sku'] , 'allow_alternative_item' , 1 )
#                 new = frappe.new_doc('Item Alternative')
#                 new.item_code = links['sku'] 
#                 new.alternative_item_code = links['linked_product_sku'] 
#                 new.insert(ignore_permissions=True)