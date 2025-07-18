import frappe 
from erpnext import get_default_currency
import requests
from io import BytesIO
import base64
from urllib.parse import urlparse
from frappe.query_builder import Order
from frappe.query_builder.functions import  Sum 
import json
from typing import Optional, Union ##


import requests
from typing import Optional, Union
import frappe

def request_with_history(
            req_method: Optional[str] = None,
            document: Optional[str] = None, 
            doctype: Optional[str] = None, 
            url: Optional[str] = None, 
            headers: Optional[Union[dict, str, float]] = None, 
            payload: Optional[Union[dict, str, float]] = None, 
            data: Optional[Union[dict, str, float]] = None,
            with_data: Optional[Union[float, int, bool]] = 0
        ):
    headers = headers or {}
    payload = payload or {}
    api = frappe.new_doc('API History')
    api.document = document
    api.doc_type = doctype
    api.url = url
    api.headers = str(headers)
    api.payload = str(payload)
    api.insert(ignore_permissions=True , ignore_mandatory=True)
    if with_data: 
        response = requests.request(req_method, url, headers=headers, data=data)
    else:
        if payload: 
            response = requests.request(req_method, url, headers=headers, json=payload)
        else:
            response = requests.request(req_method, url, headers=headers)
    api.response = str(response.content) 
    api.response_code_status = str(response.status_code)
    api.response_text = str(response.text)  
    api.save()
    return response

    

def magento_admin_details():
    setting = frappe.get_doc("Magento Setting")
    username = str(setting.username) #admintoken
    password = str(setting.password) #token1@3$
    
    return username, password
def magento_wallet_details():
    setting = frappe.get_doc("Magento Setting")
    username = str(setting.mag_wallet_user) # prasanth@theapprender.com
    password = str(setting.mag_wallet_pass) # Password123$
    
    return username, password
@frappe.whitelist()
def create_magento_auth():
    setting = frappe.get_doc("Magento Setting")
    if setting.token_generate ==1:
        base_url, headers = base_data("magento")
        username, password = magento_admin_details()
        url = f"{base_url}/rest/V1/integration/admin/token"
        payload = {
            "username": username,
            "password": password
        }
        
        response = request_with_history(req_method='POST' , 
                                        document= 'Magento Setting' , 
                                        doctype='Magento Setting' , 
                                        url=url, 
                                        headers=None, 
                                        payload=payload )
        auth = response.text.strip('"')
        # frappe.db.set_single_value( 'Magento Setting', 'magento_auth', auth, update_modified=False)
        # frappe.db.set_single_value( 'Magento Setting', 'magento_admin_prod_auth', auth, update_modified=False)
        # frappe.db.commit()
        setting.magento_admin_prod_auth = auth
        setting.magento_auth = auth
        setting.save()
        return auth

@frappe.whitelist()
def create_magento_auth_webhook():
    setting = frappe.get_doc("Magento Setting")
    if setting.auth_type == "Production":
        url = "https://miraaya-b5b31.uc.r.appspot.com/api/erp/admin/token/prod"
    elif setting.auth_type == "Develop":
        url = "https://miraaya-b5b31.uc.r.appspot.com/api/erp/admin/token/dev"
    headers = {
        "Authorization": "Bearer xmhL3cnUY+xtuCZ981sJUaDfsTmOh6dLJcdzfgbuyEU="
    }
    
    response = request_with_history(req_method='GET' , 
                                        document= 'Magento Setting' , 
                                        doctype='Magento Setting' , 
                                        url=url, 
                                        headers=headers, 
                                        )
    auth = response.text.split('"adminToken":"')[1].rstrip('"}')
    # frappe.db.set_single_value( 'Magento Setting', 'magento_admin_prod_auth', auth, update_modified=False)
    # frappe.db.set_single_value( 'Magento Setting', 'magento_auth', auth, update_modified=False)
    # frappe.db.commit()
    setting.magento_admin_prod_auth = auth
    setting.magento_auth = auth
    setting.save()
    return auth

@frappe.whitelist()
def create_magento_auth_wallet():
    base_url, headers = base_data("magento")
    username, password = magento_wallet_details()
    url = f"{base_url}/rest/V1/integration/customer/token"
    payload = {
        "username": username,
        "password": password
    }
    response = request_with_history(
                    req_method='POST',
                    doctype='Magento Setting', 
                    document='Magento Setting' , 
                    url = url , 
                    payload=payload
                    )
    auth = response.text.strip('"')
    setting = frappe.get_doc("Magento Setting")
    setting.auth_wallet = auth
    setting.save()
    return auth

@frappe.whitelist()
def create_magento_auth_wallet_webhook():
    setting = frappe.get_doc("Magento Setting")
    if setting.customer and setting.token ==1: 
        customer_doc = frappe.get_doc('Customer' , setting.customer)
        customer_email = customer_doc.custom_email
        auth = create_customer_auth(customer_email)
        setting.magento_cust_prod_auth = auth
        setting.save()
        return auth

@frappe.whitelist()
def create_customer_auth(customer_email):
    setting = frappe.get_doc("Magento Setting")
    if setting.auth_type == "Production":
        env = 'prod'
    elif setting.auth_type == "Develop":
        env = 'dev'
    else: 
        frappe.throw(
            f"Select Type of Evniroment in Magento Setting -Magento Wallet Customer Auth"
            )
    url = f"https://miraaya-b5b31.uc.r.appspot.com/api/erp/user/token/{customer_email}/{env}"
    headers = {
        'Accept': '*/*',
        'User-Agent': 'Thunder Client (https://www.thunderclient.com)',
        'Authorization': 'Bearer xmhL3cnUY+xtuCZ981sJUaDfsTmOh6dLJcdzfgbuyEU='
        }
    response = request_with_history(
        req_method='GET', 
        document='Magento Setting', 
        doctype='Magento Setting', 
        url = url, 
        headers=headers
    )
    token_json = json.loads(response.text)
    if response.status_code in [200 , 201]:
        
        if token_json.get('userToken'): 
            return token_json['userToken']
        else:
            frappe.throw(f'Error To Create User Token {str(token_json)}')
    else: 
        frappe.throw(f'Error To Create User Token {str(token_json)}')

@frappe.whitelist(allow_guest=True)
def get_payment_channel():
    c = frappe.qb.DocType('Customer')
    return (frappe.qb.from_(c)
            .where(c.custom_is_payment_channel == 1 )
            .where(c.disabled == 0 )
            .orderby("creation", order=Order.desc)
            .select(
                (c.name) , (c.customer_name) , (c.customer_group) 
            )
            ).run(as_dict =True)

@frappe.whitelist(allow_guest=True)
def get_digital_wallet():
    c = frappe.qb.DocType('Customer')
    return (frappe.qb.from_(c)
            .where(c.custom_is_digital_wallet == 1)
            .where(c.custom_is_payment_channel == 1 )
            .where(c.disabled == 0 )
            .orderby("creation", order=Order.desc)
            .select(
                (c.name) , (c.customer_name) , (c.customer_group) 
            )
            ).run(as_dict =True)
    
    
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

@frappe.whitelist(allow_guest=True)
def get_delivery_company():
    c = frappe.qb.DocType('Customer')
    return (frappe.qb.from_(c)
            .where(c.custom_is_delivery == 1 )
            .where(c.disabled == 0 )
            .orderby("creation", order=Order.desc)
            .select(
                (c.name) , (c.customer_name) , (c.customer_group) 
            )
            ).run(as_dict =True)
    
def validate_url(url):
    base_url , headers = base_data("magento")
    parsed_url = urlparse(url)
    if not parsed_url.scheme:
        url = f"{base_url}/media/catalog/product" + url
    return url

def get_max_category_id(configurable):
    category_links = configurable.get('extension_attributes', {}).get('category_links', [])
    return max((int(cat_id['category_id']) for cat_id in category_links), default=0)

def create_new_template(configurable, item_group):
    visibility_mapping = {
                        1: 'Not Visible Individually',
                        2: 'Catalog',
                        3: 'Search',
                        4: 'Catalog & Search'
                    }
    new_templete = frappe.new_doc('Item')
    new_templete.item_code = configurable['sku']
    new_templete.item_name = configurable['name']
    new_templete.custom_item_id = configurable['id']
    new_templete.item_group = item_group
    new_templete.custom_visibility = visibility_mapping.get(configurable['visibility'], '')
    new_templete.custom_magento_item_type = "configurable"
    new_templete.insert(ignore_permissions=True)
    frappe.db.set_value('Item', new_templete.name, 'has_variants', 1)
    frappe.db.set_value('Item', new_templete.name, 'custom_is_publish', 1 if configurable['status'] == 1 else 0)
    frappe.db.set_value('Item', new_templete.name, 'custom_magento_disabled', 0 if configurable['status'] == 1 else 1)
    return new_templete

def add_attributes(item_name, attributes_list):
    for options in attributes_list:
        attribute = str(options['label'])
        if not frappe.db.exists('Item Variant Attribute', {'attribute': attribute, 'parent': item_name}):
            attributes = frappe.new_doc("Item Variant Attribute")
            attributes.attribute = attribute
            attributes.parentfield = 'attributes'
            attributes.parenttype = 'Item'
            attributes.parent = item_name
            attributes.insert(ignore_permissions=True)

def add_default_variant_attributes(item_name):
    varints = ['Color', 'Size', 'Size (ml)', 'shade']
    for varint in varints:
        if not frappe.db.exists('Item Variant Attribute', {'attribute': varint, 'parent': item_name}):
            attributes = frappe.new_doc("Item Variant Attribute")
            attributes.attribute = varint
            attributes.parentfield = 'attributes'
            attributes.parenttype = 'Item'
            attributes.parent = item_name
            attributes.insert(ignore_permissions=True)
            
def set_custom_attributes(item_name, custom_attributes):
    for custom_attribute in custom_attributes:
        att_code = custom_attribute['attribute_code']
        att_value = custom_attribute['value']
        if att_value in [None, ""]:
            continue
        field_mapping = {
            "brand": "brand",
            "free_from": "custom_free_from",
            "key_features": "custom_key_features",
            "ingredients": "custom_ingredients",
            "how_to_use": "custom_how_to_use",
            "formulation": "custom_formulation",
            "product_description": "description",
            "country_of_manufacture": "custom_country_of_manufacture"
        }
        fieldname = field_mapping.get(att_code)
        if fieldname:
            frappe.db.set_value('Item', item_name, fieldname, att_value)      
@frappe.whitelist()
def upload_image_to_item( file ,  item_code , base_image):
    try:
        image_url = validate_url(file)
        
        response = request_with_history(req_method='GET' , 
                                        document='File' , 
                                        doctype= f'Atteched To Item: {item_code}',
                                        url=image_url )
        response.raise_for_status()

        image_content = BytesIO(response.content).getvalue()
        image_base64 = base64.b64encode(image_content).decode('utf-8')

        file_name = f"{file}"

        _file = frappe.get_doc({
            "doctype": "File",
            "file_name": file_name,
            "attached_to_doctype": "Item",
            "attached_to_name": item_code,
            "is_private": 0,
            "content": image_base64,
            "custom_magento_sync": 1,
            "decode": True
        })
        _file.save()
        if base_image:
            return _file.file_url
        else : 
            return 0 
    except Exception as e:
        frappe.log_error(f"Upload Image Error for item {item_code}: {e}", "Image Upload")
        return f"Upload Image Error: {e}"  

def upload_media(media_entries, templete_code):
    for media in media_entries:
        if media['media_type'] == "image":
            base_image = 1 if media['types'] else 0
            try:
                url_file = upload_image_to_item(file=media['file'], item_code=templete_code, base_image=base_image)
                if url_file:
                    frappe.db.set_value('Item', templete_code, 'image', url_file)
            except Exception as ex:
                frappe.log_error(f"Error while uploading images to item: {templete_code}. Error: {str(ex)}")      
            
def get_item_group_by_item_group_id(category_id):
    try:
        item_group_sql = frappe.db.sql("""
            SELECT name 
            FROM `tabItem Group` 
            WHERE custom_item_group_id = %s
        """, (str(category_id)), as_dict=True)
        if item_group_sql and item_group_sql[0] and item_group_sql[0]['name']:
            return item_group_sql[0]['name']
        else:
            create_item_group()
            item_group_sql = frappe.db.sql("""
                SELECT name 
                FROM `tabItem Group` 
                WHERE custom_item_group_id = %s
            """, (str(category_id)), as_dict=True)
            if item_group_sql and item_group_sql[0] and  item_group_sql[0]['name']:
                return item_group_sql[0]['name']
            else:
                return None
    except Exception as ex:
        return (f"Error in get_item_group_by_item_group_id: {str(ex)}")
        
    
def base_data(request_in ,customer_email = None):
    if request_in == "magento":
        setting = frappe.get_doc("Magento Setting")
        if setting.token:
            auth = setting.magento_admin_prod_auth
        else:
            auth = setting.magento_auth
        base_url = str(setting.magento_url).strip()
        headers = {
            "Authorization": f"Bearer {str(auth).strip()}",
            "Content-Type": "application/json"
        }
        return base_url , headers
    elif request_in == "magento_customer_auth" and  customer_email is not None :
        auth = create_customer_auth(customer_email)
        setting = frappe.get_doc("Magento Setting")
        base_url = str(setting.url_wallet).strip()
        headers = {
            "Authorization": f"Bearer {auth}",
            "Content-Type": "application/json"
        }
        return base_url , headers
    elif request_in == "frappe":
        setting = frappe.get_doc("Magento Setting")
        base_url = str(setting.frappe_url).strip()
        headers = {
            "Authorization": f"Basic {str(setting.frappe_auth).strip()}",
            "Content-Type": "application/json"
        }
        return base_url , headers    
    elif request_in == "webhook":
        base_url = 'https://miraaya-b5b31.uc.r.appspot.com/api/erp'
        headers = {
                'Accept': '*/*',
                'Authorization': 'Bearer xmhL3cnUY+xtuCZ981sJUaDfsTmOh6dLJcdzfgbuyEU=',
                'Content-Type': 'application/json'
            }
        return base_url , headers

def insert_item_price(
        item_code ,
        brand,
        uom , 
        rate 
    ):
    price_list_sql = frappe.db.sql("SELECT name FROM `tabPrice List` tpl WHERE selling =1 AND custom_magento_selling =1 " , as_dict = True)
    if price_list_sql and price_list_sql[0] and price_list_sql[0]['name']:
        price_list = price_list_sql[0]['name']
    else: 
        price_list_sql_selling = frappe.db.sql("SELECT name FROM `tabPrice List` tpl WHERE selling =1" , as_dict = True)
        price_list = price_list_sql_selling[0]['name']
        
    item_price = frappe.get_doc(
				{
					"doctype": "Item Price",
					"price_list": price_list,
					"item_code":item_code,
					"uom": uom,
					"brand": brand,
					"currency": get_default_currency(),
					"price_list_rate": float(rate),
				}
			)
    item_price.insert()
    frappe.db.set_value("Item Price" ,item_price.name , 'custom_publish_to_magento' , 1 )
    frappe.db.commit()

@frappe.whitelist()
def sync_magento_products():
    
    try: 
        base_url, headers = base_data("magento")
        url = base_url + "/rest/V1/products?searchCriteria="
        request = request_with_history(req_method='GET', 
                                       doctype='Sync To Barnd', 
                                       document='Brand', 
                                       headers=headers, 
                                       url=url)        
        json_response = request.json()
    except Exception as ex:
        return f"Error in Magento Connection : {str(ex)}"
    ####### Chech for Brand And Item Group 
    try:
        frappe.enqueue(
            'masar_miraaya.api.get_magento_brand',
            queue='long',
            timeout=5000,
            is_async=True,
            enqueue_after_commit=True,
            at_front=True,
            response_json =json_response
        )
    except Exception as ex:
        return f"Error While Sync with Brand {str(ex)}"
    
@frappe.whitelist()
def get_magento_brand(response_json = None):
    try:
        create_item_group()
    except Exception as ex : 
        return "Exception Sync Item Group from Brands :" + str(ex) 
    try:
        brands = frappe.db.sql("""SELECT item_group_name FROM `tabItem Group` tig WHERE custom_parent_item_group_id = '404' """, as_dict = True)
        for brand in brands:
            brand_name = brand['item_group_name'].split(' - ', 1)[-1].strip()
            exist_brands = frappe.db.sql("""SELECT name FROM `tabBrand` WHERE name = %s""" , (brand_name) , as_dict = 1 )
            if not (exist_brands and exist_brands[0] and exist_brands[0]['name']): 
                new_brand = frappe.new_doc('Brand')
                new_brand.brand = brand_name
                new_brand.insert(ignore_permissions=True)
                frappe.db.set_value("Brand" ,new_brand.name , 'custom_publish_to_magento' , 1 )
                frappe.db.commit()
    except Exception as e:
        return (f"General Error: {e}", "Magento Sync")
    if response_json:
        all_items = response_json['items']
        all_configurable_links = list()
        altenative_items = list()
        all_simple = list()
        all_configurable = list()
        for item in all_items:
            if item['type_id'] == "configurable":
                templete_code = item['sku']
                templete_id = item['id']
                links_product = item['extension_attributes']['configurable_product_links']
                all_configurable_links.append(frappe._dict(
                            {
                            'templete_code' : templete_code, 
                            'templete_id' : templete_id,
                            'links_product' : links_product
                            }
                        )
                    )
            if item['type_id'] == "simple":
                all_simple.append(item)
            if item['type_id'] == "configurable":
                all_configurable.append(item)
            if len(item["product_links"]) !=0:
                altenative_items.append(frappe._dict({'links_product' : item["product_links"], }))
            
        frappe.enqueue(
            'masar_miraaya.api.get_magento_item_attributes',
            queue='long',
            timeout=5000,
            is_async=True,
            enqueue_after_commit=True,
            at_front=True,
            all_simple = all_simple , 
            all_configurable_links  = all_configurable_links , 
            all_configurable = all_configurable , 
            altenative_items = altenative_items
        ) 
    else:
        frappe.msgprint("Sync Completed Successfully." , alert=True , indicator='green')
    
        
@frappe.whitelist()
def create_item_group():
    try:
        base_url, headers =  base_data("magento")
        url = f"{base_url}/rest/all/V1/categories"
        request = request_with_history(
                    req_method='GET', 
                    document='Item Group', 
                    doctype='Sync to Item Group', 
                    url=url, 
                    headers=headers        
                )
        magento_categories =  request.json()
        existing_root_item_group = frappe.db.sql("SELECT name FROM `tabItem Group` WHERE custom_parent_item_group_id = 0 " , as_dict=True)
        if not(existing_root_item_group and existing_root_item_group[0] and existing_root_item_group[0]['name']):
            root_category = magento_categories['name']
            root_id = magento_categories['id']
            root_parent_id = magento_categories['parent_id']
            root_status = 1
            root_unique_name = f"{root_id} - {root_category}"
            new_root = frappe.new_doc('Item Group')
            new_root.item_group_name = root_unique_name
            new_root.parent_item_group = None
            new_root.custom_item_group_id = root_id
            new_root.custom_parent_item_group_id = root_parent_id
            new_root.is_group = 1
            new_root.save(ignore_permissions = True)
            frappe.db.set_value("Item Group" ,new_root.name , 'custom_is_publish' , root_status )
            frappe.db.commit()
        else: 
            root_unique_name = existing_root_item_group[0]['name']
        if len(magento_categories['children_data']) !=0:
            create_item_group_childs_loop(root_unique_name  , magento_categories['children_data'])
            return "Sync Item Group Successfully"
    except Exception as e:
        return f"Create Item Group Error: {str(e)}"

def create_item_group_childs_loop(parent , children_data_list):
    for children_data in children_data_list:
        create_item_group_childs(parent , children_data)

def create_item_group_childs(parent , children_data): 
        category_name = children_data['name']
        category_id = children_data['id']
        parent_id = children_data['parent_id']
        category_status = 1 if children_data['is_active'] else 0
        if len(children_data['children_data']) !=0:
            is_group = 1 
        else : 
            is_group = 0 
        unique_name = f"{category_id} - {category_name}"
        existing_item_group = frappe.db.sql("SELECT name , parent_item_group FROM `tabItem Group` WHERE name = %s " , (unique_name) , as_dict = True)
        if existing_item_group and existing_item_group[0]:
            if existing_item_group[0]['parent_item_group'] != parent:
                update_parent = frappe.get_doc('Item Group' ,existing_item_group[0]['name'] )
                update_parent.parent_item_group = parent
                update_parent.save(ignore_permissions = True)
                frappe.db.set_value("Item Group" ,existing_item_group[0]['name'] , 'parent_item_group' , parent )
                frappe.db.commit()
        else:
            new_root = frappe.new_doc('Item Group')
            new_root.item_group_name = unique_name
            new_root.parent_item_group = parent
            new_root.custom_item_group_id = category_id
            new_root.custom_parent_item_group_id = parent_id
            new_root.is_group = is_group
            new_root.save(ignore_permissions = True)
            frappe.db.set_value("Item Group" ,new_root.name , 'custom_is_publish' , category_status )
            frappe.db.commit() 
        if  is_group:
             create_item_group_childs_loop(unique_name , children_data['children_data'])
             
             
@frappe.whitelist()
def get_magento_item_attributes(all_simple= None , all_configurable_links = None , all_configurable = None , altenative_items = None):
    base_url, headers = base_data("magento")
    url = base_url + "/rest/V1/products/attributes?searchCriteria[pageSize]=100"
    
    response = request_with_history(
                        req_method='GET', 
                        doctype='Item Attributes' , 
                        document='Sync to Item Attributes', 
                        url=url, 
                        headers=headers)
    json_response = response.json()
    attributes = json_response['items']
    for attribute in attributes:
        process_item_attribute(attribute)

    if all_simple or all_configurable or altenative_items or all_configurable_links:
        frappe.enqueue(
            'masar_miraaya.api.create_templete_items',
            queue='long',
            timeout=7000,
            is_async=True,
            enqueue_after_commit=True,
            at_front=True,
            all_simple=all_simple ,
            all_configurable_links = all_configurable_links,
            all_configurable = all_configurable,
            altenative_items = altenative_items,
        )
    else:
        frappe.msgprint("Sync Completed Successully." , alert=True , indicator=True)
    
    
def process_item_attribute(attribute):
    allowed_apply_to_values = ['simple', 'virtual', 'downloadable', 'bundle', 'configurable']
    try:
        default_frontend_label = attribute.get('default_frontend_label')
        if default_frontend_label:
            exist_attributes = frappe.db.sql(
                "SELECT name FROM `tabAttributes` WHERE default_frontend_label = %s",
                (default_frontend_label),
                as_dict=True
            )

            if not (exist_attributes and exist_attributes[0] and exist_attributes[0].get('name')):
                new_attribute = frappe.new_doc('Attributes')
                new_attribute.default_frontend_label = str(default_frontend_label)
                new_attribute.is_wysiwyg_enabled = attribute.get('is_wysiwyg_enabled', False)
                new_attribute.is_html_allowed_on_front = attribute.get('is_html_allowed_on_front', False)
                new_attribute.used_for_sort_by = attribute.get('used_for_sort_by', False)
                new_attribute.is_filterable = attribute.get('is_filterable', False)
                new_attribute.is_filterable_in_search = attribute.get('is_filterable_in_search', False)
                new_attribute.is_used_in_grid = attribute.get('is_used_in_grid', False)
                new_attribute.is_visible_in_grid = attribute.get('is_visible_in_grid', False)
                new_attribute.is_filterable_in_grid = attribute.get('is_filterable_in_grid', False)
                new_attribute.apply_to = str(attribute.get('apply_to', ''))
                new_attribute.is_searchable = attribute.get('is_searchable', False)
                new_attribute.is_visible_in_advanced_search = attribute.get('is_visible_in_advanced_search', False)
                new_attribute.is_comparable = attribute.get('is_comparable', False)
                new_attribute.is_used_for_promo_rules = attribute.get('is_used_for_promo_rules', False)
                new_attribute.is_visible_on_front = attribute.get('is_visible_on_front', False)
                new_attribute.used_in_product_listing = attribute.get('used_in_product_listing', False)
                new_attribute.scope = attribute.get('scope', '')
                new_attribute.is_visible = attribute.get('is_visible', False)
                new_attribute.attribute_code = attribute.get('attribute_code', '')
                new_attribute.is_required = attribute.get('is_required', False)

                if attribute.get('default_value'):
                    new_attribute.default_value = attribute.get('default_value')
                    new_attribute.append('att_details', {
                        'label': 'Default', 'value': attribute.get('default_value')
                    })
                else:  
                    if attribute.get('default_value') in ["" , " " , None] or not  attribute.get('default_value'):
                        new_attribute.append('att_details', {
                            'label': 'Default', 'value': "default"
                        })
                for option in attribute.get('options', []):
                    if (option.get('value') not in [None, "", '', 0, ' ', " "]) and (option.get('label') not in [None, "", '', 0, " ", ' ']):
                        existing_attribute_value = frappe.db.get_value('Attributes Details', {
                            'parent': default_frontend_label,
                            'label': str(option.get('label'))
                        }, 'name')
                        if not existing_attribute_value:
                            new_attribute.append('att_details', {
                                'label': option.get('label'),
                                'value': option.get('value')
                            })

                new_attribute.insert(ignore_permissions=True)
                apply_to_values = attribute.get('apply_to', [])
                if any(value in allowed_apply_to_values for value in apply_to_values) or default_frontend_label in ['Color' , 'Size' , 'Size (ml)' , 'shade'] :
                        if frappe.db.exists('Item Attribute', default_frontend_label):
                            item_attribute = frappe.get_doc('Item Attribute', default_frontend_label)
                        else:
                            item_attribute = frappe.new_doc('Item Attribute')
                            item_attribute.attribute_name = default_frontend_label
                            item_attribute.custom_attribute_code = attribute.get('attribute_code', '')
                            item_attribute.insert(ignore_permissions=True)
                            frappe.db.set_value("Item Attribute" ,item_attribute.name , 'custom_publish_to_magento' , 1 )
                            frappe.db.commit()
                            
                        if attribute.get('default_value'):
                            existing_default_value = frappe.db.get_value('Item Attribute Value', {
                                    'parent': default_frontend_label,
                                    'attribute_value': str(option.get('label'))
                                }, 'name')
                            if not existing_default_value:
                                    new_attribute_value = frappe.new_doc('Item Attribute Value')
                                    new_attribute_value.attribute_value =  'Default'
                                    new_attribute_value.abbr = str( attribute.get('default_value'))
                                    new_attribute_value.parent = default_frontend_label
                                    new_attribute_value.parentfield = 'item_attribute_values'
                                    new_attribute_value.parenttype = 'Item Attribute'
                                    new_attribute_value.insert(ignore_permissions=True)
                        else:  
                            if attribute.get('default_value') in ["" , " " , None] or not  attribute.get('default_value'):
                                existing_default_value = frappe.db.get_value('Item Attribute Value', {
                                    'parent': default_frontend_label,
                                    'attribute_value': str(option.get('label'))
                                }, 'name')
                            if not existing_default_value:
                                    new_attribute_value = frappe.new_doc('Item Attribute Value')
                                    new_attribute_value.attribute_value =  'Default'
                                    new_attribute_value.abbr = str('default')
                                    new_attribute_value.parent = default_frontend_label
                                    new_attribute_value.parentfield = 'item_attribute_values'
                                    new_attribute_value.parenttype = 'Item Attribute'
                                    new_attribute_value.insert(ignore_permissions=True)
                        
                        for option in attribute.get('options', []):
                            if (option.get('value') not in [None, "", '', 0, ' ', " "]) and (option.get('label') not in [None, "", '', 0, " ", ' ']):
                                existing_attribute_value = frappe.db.get_value('Item Attribute Value', {
                                    'parent': default_frontend_label,
                                    'attribute_value': str(option.get('label'))
                                }, 'name')
                                if not existing_attribute_value:
                                    new_attribute_value = frappe.new_doc('Item Attribute Value')
                                    new_attribute_value.attribute_value = str(option.get('label'))
                                    new_attribute_value.abbr = str(option.get('value'))
                                    new_attribute_value.parent = default_frontend_label
                                    new_attribute_value.parentfield = 'item_attribute_values'
                                    new_attribute_value.parenttype = 'Item Attribute'
                                    new_attribute_value.insert(ignore_permissions=True)
                        
    except Exception as e:
        return f"Error processing attribute {attribute.get('default_frontend_label', 'Unknown')}: {e}"
    


def create_templete_items(all_simple,all_configurable_links,  all_configurable, altenative_items):
    item_codes = [item['sku'] for item in all_configurable if item['type_id'] == "configurable"]
    existing_templates = frappe.get_all('Item', filters={'item_code': ['in', item_codes]}, fields=['item_code', 'name'])
    existing_templates_dict = {item['item_code']: item['name'] for item in existing_templates}
    for configurable in all_configurable:

        if configurable['type_id'] != "configurable":
            continue

        templete_code = configurable['sku']
        if templete_code in existing_templates_dict:
            continue 

        category_id_max = get_max_category_id(configurable)
        item_group = get_item_group_by_item_group_id(category_id_max) if category_id_max else ''

        new_templete = create_new_template(configurable, item_group)
        add_attributes(new_templete.name, configurable['extension_attributes'].get('configurable_product_options', []))
        add_default_variant_attributes(new_templete.name)
        set_custom_attributes(new_templete.name, configurable.get('custom_attributes', []))
        upload_media(configurable.get('media_gallery_entries', []), templete_code)
    get_magento_products_in_enqueue(all_simple, all_configurable_links , altenative_items)
    
def get_magento_products_in_enqueue(all_simple , all_configurable_links, altenative_items):
    batch_size = 100
    total_items = len(all_simple)
    final_loop = False
    for i in range(0, len(all_simple), batch_size):
        if i + batch_size >= total_items:
            final_loop = True
        batch = all_simple[i:i + batch_size]
        frappe.enqueue(
            'masar_miraaya.api.get_magento_products',
            queue='long',
            timeout=5000,
            is_async=True,
            enqueue_after_commit=True,
            at_front=True,
            response_json={'items': batch} ,
            all_configurable_links = all_configurable_links ,  
            altenative_items = altenative_items , 
            final_loop = final_loop
        )
        
        

def get_magento_products(response_json, all_configurable_links, altenative_items , final_loop):
    try:
        all_items = response_json['items']
        for item in all_items:
            if item['type_id'] == "simple":
                category_id_max = 0 
                item_id = item['id']
                item_code = item['sku']
                item_name = item['name']
                rate = item['price']
                exist_item_code = frappe.db.sql("SELECT name FROM `tabItem` WHERE item_code = %s", (item_code,), as_dict=True)

                if not (exist_item_code and exist_item_code[0] and exist_item_code[0]['name']):
                    visibility_mapping = {
                        1: 'Not Visible Individually',
                        2: 'Catalog',
                        3: 'Search',
                        4: 'Catalog & Search'
                    }
                    visibility = visibility_mapping.get(item['visibility'], '')
                    
                    if item['extension_attributes'] and item['extension_attributes']['category_links']:
                        category_links = item['extension_attributes']['category_links']
                        for cat_id in category_links:
                            category_id = int(cat_id['category_id'])
                            if category_id_max == 0 or category_id > category_id_max:
                                category_id_max = category_id
                    if category_id_max:
                        item_group = get_item_group_by_item_group_id(category_id_max)
                    
                    if item['status'] == 1:
                        publish_to_magento = 1 
                        disabled = 0 
                    elif item['status'] == 2:
                        publish_to_magento = 0
                        disabled = 1 
                    
                    # Create new Item document
                    new_item_ = frappe.new_doc('Item')
                    new_item_.item_code = item_code
                    new_item_.item_name = item_name
                    new_item_.custom_item_id = item_id
                    new_item_.item_group = item_group
                    new_item_.custom_visibility = visibility
                    new_item_.custom_magento_item_type = "simple"
                    new_item_.insert(ignore_permissions=True)
                    # Set additional values
                    frappe.db.set_value('Item', new_item_.name, 'custom_is_publish', publish_to_magento)
                    frappe.db.set_value('Item', new_item_.name, 'custom_magento_disabled', disabled)
                    
                    # Variant processing
                    for configurable in all_configurable_links:
                        link_product = configurable['links_product']
                        if item_id in link_product:
                            variant_item_sql = frappe.db.sql("SELECT name FROM tabItem WHERE item_code = %s", (configurable['templete_code'],), as_dict=True)
                            if variant_item_sql and variant_item_sql[0] and variant_item_sql[0]['name']:
                                frappe.db.set_value('Item', new_item_.name, 'variant_of', variant_item_sql[0]['name'])
                    
                    # Custom attributes processing
                    for custom_attributes in item['custom_attributes']:
                        att_code = custom_attributes['attribute_code']
                        att_value = custom_attributes['value']
                        if att_code == "brand":
                            brand_sql = frappe.db.sql("SELECT name FROM `tabBrand` WHERE name = %s", (att_value,), as_dict=True)
                            if brand_sql and brand_sql[0] and brand_sql[0]['name']:
                                brand = brand_sql[0]['name']
                            else:
                                new_brand = frappe.new_doc('Brand')
                                new_brand.brand = att_value
                                new_brand.insert(ignore_permissions=True)
                                frappe.db.set_value("Brand" ,new_brand.name , 'custom_publish_to_magento' , 1 )
                                frappe.db.commit()
                                brand = new_brand.name
                            new_item_.brand = brand
                        if att_code == "free_from" and att_value:
                            frappe.db.set_value('Item', new_item_.name, 'custom_free_from', att_value)
                        if att_code == "key_features" and att_value:
                            frappe.db.set_value('Item', new_item_.name, 'custom_key_features', att_value)
                        if att_code == "ingredients" and att_value:
                            frappe.db.set_value('Item', new_item_.name, 'custom_ingredients', att_value)
                        if att_code == "how_to_use" and att_value:
                            frappe.db.set_value('Item', new_item_.name, 'custom_how_to_use', att_value)
                        if att_code == "formulation" and att_value:
                            frappe.db.set_value('Item', new_item_.name, 'custom_formulation', att_value)
                        if att_code == "product_description" and att_value:
                            frappe.db.set_value('Item', new_item_.name, 'description', att_value)
                        ####
                        if att_code == "arabic_name" and att_value:
                            frappe.db.set_value('Item', new_item_.name, 'custom_item_name_ar', att_value)
                        if att_code == "arabic_metatitle" and att_value:
                            frappe.db.set_value('Item', new_item_.name, 'custom_arabic_metatitle', att_value)
                        if att_code == "arabic_description" and att_value:
                            frappe.db.set_value('Item', new_item_.name, 'custom_arabic_description', att_value)
                        if att_code == "arabic_country" and att_value:
                            frappe.db.set_value('Item', new_item_.name, 'custom_arabic_country', att_value)
                        if att_code == "arabic_meta_keywords" and att_value:
                            frappe.db.set_value('Item', new_item_.name, 'custom_arabic_meta_keywords', att_value)
                        if att_code == "arabic_meta_description" and att_value:
                            frappe.db.set_value('Item', new_item_.name, 'custom_arabic_meta_description', att_value)
                        if att_code == "arabic_howtouse" and att_value:
                            frappe.db.set_value('Item', new_item_.name, 'custom_arabic_howtouse', att_value)
                        if att_code == "arabic_testresult" and att_value:
                            frappe.db.set_value('Item', new_item_.name, 'custom_arabic_test_result', att_value)
                        if att_code == "arabic_ingredients" and att_value:
                            frappe.db.set_value('Item', new_item_.name, 'custom_arabic_ingredients', att_value)
                        if att_code == "article_no" and att_value:
                            frappe.db.set_value('Item', new_item_.name, 'custom_article_no', att_value)
                        if att_code == "meta_title" and att_value:
                            frappe.db.set_value('Item', new_item_.name, 'custom_meta_title', att_value)
                        if att_code == "meta_keyword" and att_value:
                            frappe.db.set_value('Item', new_item_.name, 'custom_meta_keyword', att_value)
                        if att_code == "meta_description" and att_value:
                            frappe.db.set_value('Item', new_item_.name, 'custom_meta_description', att_value)
                        if att_code == "warning_quantity" and att_value:
                            frappe.db.set_value('Item', new_item_.name, 'custom_warning_quantity', att_value)
                        if att_code == "country_of_manufacture" and att_value:
                            country_id_sql = frappe.db.sql("SELECT name FROM tabCountry WHERE code = %s" , (att_value.lower()) , as_dict = True)
                            if country_id_sql and country_id_sql[0] and country_id_sql[0]['name']:
                                country = country_id_sql[0]['name']
                            
                            frappe.db.set_value('Item', new_item_.name, 'custom_country_of_manufacture', country)

                        #Handling item attributes for variants
                        if att_code in ['color', 'size_ml', 'shade', 'size']:
                            attribute_value = frappe.db.sql("""
                            SELECT tia.name , tav.attribute_value FROM `tabItem Attribute` tia 
                                        INNER JOIN  `tabItem Attribute Value` tav ON tia.name = tav.parent 
                                        WHERE tav.abbr = %s OR tav.attribute_value =  %s
                                        """, (str(att_value),str(att_value)), as_dict=True)                          
                            if attribute_value and attribute_value[0] and attribute_value[0]['attribute_value']:
                                variant = attribute_value[0]['attribute_value']
                            else:
                                variant_sql = frappe.db.sql("""
                                SELECT tia.name , tav.attribute_value FROM `tabItem Attribute` tia 
                                            INNER JOIN  `tabItem Attribute Value` tav ON tia.name = tav.parent 
                                            WHERE tav.abbr = %s OR tav.attribute_value =  %s
                                            """, ("default","Default"), as_dict=True)
                                if  variant_sql and variant_sql[0] and variant_sql[0]['attribute_value']:
                                    variant = variant_sql[0]['attribute_value']
                                else:
                                   variant = att_value 
                            if att_code == 'color':
                                frappe.db.set_value('Item', new_item_.name, 'custom_color', variant)
                            if att_code == 'size':
                                frappe.db.set_value('Item', new_item_.name, 'custom_size', variant)

                            if att_code == 'shade':
                                frappe.db.set_value('Item', new_item_.name, 'custom_shade', variant)

                            if att_code == 'size_ml':
                                frappe.db.set_value('Item', new_item_.name, 'custom_size_ml', variant)

                            item_attribute_sql = frappe.db.sql("SELECT custom_attribute_code FROM `tabItem Attribute`", as_dict=True)
                            for item_attribute in item_attribute_sql:
                                if att_code == item_attribute.custom_attribute_code:
                                    attribute_value = frappe.db.sql("""
                                        SELECT tia.name , tav.attribute_value FROM `tabItem Attribute` tia 
                                        INNER JOIN  `tabItem Attribute Value` tav ON tia.name = tav.parent 
                                        WHERE tav.abbr = %s OR tav.attribute_value =  %s
                                    """, (str(att_value),str(att_value)), as_dict=True)

                                    # if attribute_value:
                                    new_att = frappe.new_doc('Item Variant Attribute')
                                    new_att.attribute = str(attribute_value[0]['name'])
                                    new_att.attribute_value = str(attribute_value[0]['attribute_value'])
                                    new_att.variant_of = new_item_.variant_of
                                    new_att.parent = new_item_.name
                                    new_att.parentfield = 'attributes'
                                    new_att.parenttype = 'Item'
                                    new_att.insert(ignore_permissions=True , ignore_mandatory=True)
                                    
                                    frappe.db.commit()

                    # Process images
                    try:
                        for media in item['media_gallery_entries']:
                            if media['media_type'] == "image":
                                base_image = 1 if 'thumbnail' in media['types'] else 0
                                url_file = upload_image_to_item(
                                    file=media['file'], 
                                    item_code=item_code,
                                    base_image=base_image
                                )
                                if url_file:
                                    frappe.db.set_value('Item', new_item_.name, 'image', url_file)
                    except Exception as ex:
                        return f"Error While uploading Images to item: {str(ex)}"
                    
                    insert_item_price(
                            item_code=new_item_.name ,
                            uom = new_item_.stock_uom , 
                            brand = brand,
                            rate = str(rate)
                        )  
                    frappe.db.commit()  # Ensure all operations are committed
                else:
                    item_exist_doc = frappe.get_doc('Item' , exist_item_code[0]['name']) 
                    for custom_attributes in item['custom_attributes']:
                        att_code = custom_attributes['attribute_code']
                        att_value = custom_attributes['value']
                        if att_code == "brand":
                            brand_sql = frappe.db.sql("SELECT name FROM `tabBrand` WHERE name = %s", (att_value,), as_dict=True)
                            if brand_sql and brand_sql[0] and brand_sql[0]['name']:
                                brand = brand_sql[0]['name']
                            else:
                                new_brand = frappe.new_doc('Brand')
                                new_brand.brand = att_value
                                new_brand.insert(ignore_permissions=True)
                                frappe.db.set_value("Brand" ,new_brand.name , 'custom_publish_to_magento' , 1 )
                                frappe.db.commit()
                                brand = new_brand.name
                            item_exist_doc.brand = brand
                        if att_code == "free_from" and att_value:
                            frappe.db.set_value('Item', item_exist_doc.name, 'custom_free_from', att_value)
                        if att_code == "key_features" and att_value:
                            frappe.db.set_value('Item', item_exist_doc.name, 'custom_key_features', att_value)
                        if att_code == "ingredients" and att_value:
                            frappe.db.set_value('Item', item_exist_doc.name, 'custom_ingredients', att_value)
                        if att_code == "how_to_use" and att_value:
                            frappe.db.set_value('Item', item_exist_doc.name, 'custom_how_to_use', att_value)
                        if att_code == "formulation" and att_value:
                            frappe.db.set_value('Item', item_exist_doc.name, 'custom_formulation', att_value)
                        if att_code == "product_description" and att_value:
                            frappe.db.set_value('Item', item_exist_doc.name, 'description', att_value)
                        if att_code == "arabic_name" and att_value:
                            frappe.db.set_value('Item', item_exist_doc.name, 'custom_item_name_ar', att_value)
                        if att_code == "arabic_metatitle" and att_value:
                            frappe.db.set_value('Item', item_exist_doc.name, 'custom_arabic_metatitle', att_value)
                        if att_code == "arabic_description" and att_value:
                            frappe.db.set_value('Item', item_exist_doc.name, 'custom_arabic_description', att_value)
                        if att_code == "arabic_country" and att_value:
                            frappe.db.set_value('Item', item_exist_doc.name, 'custom_arabic_country', att_value)
                        if att_code == "arabic_meta_keywords" and att_value:
                            frappe.db.set_value('Item', item_exist_doc.name, 'custom_arabic_meta_keywords', att_value)
                        if att_code == "arabic_meta_description" and att_value:
                            frappe.db.set_value('Item', item_exist_doc.name, 'custom_arabic_meta_description', att_value)
                        if att_code == "arabic_howtouse" and att_value:
                            frappe.db.set_value('Item', item_exist_doc.name, 'custom_arabic_howtouse', att_value)
                        if att_code == "arabic_testresult" and att_value:
                            frappe.db.set_value('Item', item_exist_doc.name, 'custom_arabic_test_result', att_value)
                        if att_code == "arabic_ingredients" and att_value:
                            frappe.db.set_value('Item', item_exist_doc.name, 'custom_arabic_ingredients', att_value)
                        if att_code == "article_no" and att_value:
                            frappe.db.set_value('Item', item_exist_doc.name, 'custom_article_no', att_value)
                        if att_code == "meta_title" and att_value:
                            frappe.db.set_value('Item', item_exist_doc.name, 'custom_meta_title', att_value)
                        if att_code == "meta_keyword" and att_value:
                            frappe.db.set_value('Item', item_exist_doc.name, 'custom_meta_keyword', att_value)
                        if att_code == "meta_description" and att_value:
                            frappe.db.set_value('Item', item_exist_doc.name, 'custom_meta_description', att_value)
                        if att_code == "warning_quantity" and att_value:
                            frappe.db.set_value('Item', item_exist_doc.name, 'custom_warning_quantity', att_value)
                        if att_code == "country_of_manufacture" and att_value:
                            country_id_sql = frappe.db.sql("SELECT name FROM tabCountry WHERE code = %s" , (att_value.lower()) , as_dict = True)
                            if country_id_sql and country_id_sql[0] and country_id_sql[0]['name']:
                                country = country_id_sql[0]['name']
                            frappe.db.set_value('Item', item_exist_doc.name, 'custom_country_of_manufacture', country)
        if final_loop and altenative_items:
            frappe.enqueue(
                'masar_miraaya.api.get_alternative_items',
                queue='long',
                timeout=5000,
                is_async=True,
                enqueue_after_commit=True,
                at_front=True,
                altenative_items=altenative_items
            )

    except Exception as ex:
        return f"Exception in get_magento_products: {str(ex)}"
    
    
def get_alternative_items(altenative_items):
    for altenative in altenative_items: 
        for links in altenative['links_product']:
            if links["link_type"] == "related": 
                frappe.db.set_value('Item' , links['sku'] , 'allow_alternative_item' , 1 )
                frappe.db.set_value('Item' , links['linked_product_sku'] , 'allow_alternative_item' , 1 )
                new = frappe.new_doc('Item Alternative')
                new.item_code = links['sku'] 
                new.alternative_item_code = links['linked_product_sku'] 
                new.insert(ignore_permissions=True)
                frappe.db.set_value('Item Alternative' , new.name , 'custom_is_publish' , 1 )
                frappe.db.commit()
                     
@frappe.whitelist()
def get_magento_customers():
    try:
        get_customer_group()
        base_url, headers = base_data("magento")
        url = base_url + "/rest/V1/customers/search?searchCriteria="
        request = request_with_history(
                            req_method='GET', 
                            doctype='Customer', 
                            document='Sync to Customer', 
                            url=url, 
                            headers=headers)
        json_response = request.json()
        customers = json_response['items']

        for customer in customers:
            customer_id = customer['id']
            customer_group_id = customer['group_id']
            customer_default_shipping_id = customer.get('default_shipping', "")
            customer_default_billing_id = customer.get('default_billing', "")
            customer_group_name = get_customer_group_name(customer_group_id)
            customer_first_name = customer.get('firstname', "")
            customer_middle_name = customer.get('middlename', "")
            customer_tax_id = customer.get('taxvat', "")
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
                                               (customer_name, customer_id), as_dict=True)
                                               
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
                new_customer.disabled = 0
                new_customer.tax_id = customer_tax_id
                new_customer.tax_category = 'Retail Customer'
                new_customer.custom_website_id = website_id
                new_customer.custom_store_id = store_id
                new_customer.custom_date_of_birth = customer_dob
                new_customer.custom_default_billing_id = customer_default_billing_id
                new_customer.custom_default_shipping_id = customer_default_shipping_id
                new_customer.save(ignore_permissions=True)
                frappe.db.set_value("Customer" ,new_customer.name , 'custom_is_publish' , 1 )
                
            if len(customer['addresses']) != 0 :   
                create_customer_address(customer['addresses'] , customer_email)
                primary_address_sql = frappe.db.sql("SELECT name FROM tabAddress WHERE custom_address_id = %s" ,((customer_default_billing_id)) , as_dict = True)
                if primary_address_sql and primary_address_sql[0] and primary_address_sql[0]['name']:
                    frappe.db.set_value("Customer" ,new_customer.name , 'customer_primary_address' ,primary_address_sql[0]['name'] )
                frappe.db.commit()
                new_customer.reload()
        return "Customers Created Successfully"
    except Exception as e:
        return f"Error get customers: {e}"
    
@frappe.whitelist()
def get_customer_group():
    try:
        base_url, headers = base_data("magento")
        base_url_frappe, headers_frappe = base_data("frappe")
        
        existing_customer_group = frappe.db.sql("Select name FROM `tabCustomer Group` WHERE name = 'All Customer Groups'", as_dict = True)
        if not (existing_customer_group and existing_customer_group[0] and existing_customer_group[0]['name']):
            new_customer_group = frappe.new_doc('Customer Group')
            new_customer_group.customer_group_name = "All Customer Groups"
            new_customer_group.is_group = 1
            new_customer_group.custom_customer_group_id = 99999
            new_customer_group.save(ignore_permissions=True)
            frappe.db.set_value("Customer Group" ,new_group.name , 'custom_is_publish' , 1 )
            frappe.db.commit()
            
        url = base_url + "/rest/V1/customerGroups/search?searchCriteria="
        request = request_with_history(
                            req_method='GET', 
                            doctype='Customer Group', 
                            document='Sync to Customer Group', 
                            url=url, 
                            headers=headers)
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
                frappe.db.set_value("Customer Group" ,new_group.name , 'custom_is_publish' , 1 )
                frappe.db.commit()
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
    if customer_group:    
        return customer_group
    else: 
        base_url, headers = base_data("magento")
        url = base_url + f"/rest/V1/customerGroups/{id}"
        request = request_with_history(
                            req_method='GET', 
                            doctype='Customer Group', 
                            document=id, 
                            url=url, 
                            headers=headers)
        json_response = request.json()
        if json_response:
            new_group = frappe.get_doc('Customer Group')
            new_group.customer_group_name =  json_response['code']
            new_group.custom_customer_group_id = json_response['id']
            new_group.parent_customer_group = "All Customer Groups"
            new_group.save(ignore_permissions=True)
            frappe.db.set_value("Customer Group" ,new_group.name , 'custom_is_publish' , 1 )
            frappe.db.commit()
            existing_tax_group = frappe.db.sql("Select name FROM `tabTax Category` WHERE name = %s", (json_response['tax_class_name']), as_dict = True)
            if not (existing_tax_group and existing_tax_group[0] and existing_tax_group[0]['name']):
                new_tax_group = frappe.new_doc('Tax Category')
                new_tax_group.title = json_response['tax_class_name']
                new_tax_group.custom_tax_category_id = json_response['tax_class_id']
                new_tax_group.save(ignore_permissions=True)
        return new_group.name
    
def create_customer_address(adresses , customer_email):
                for address in adresses:
                    address_id = address['id']
                    address_line = address['street'][0]
                    city = address['city']
                    pincode = address['postcode']
                    phone = address['telephone']
                    email_id = customer_email
                    first_name = address.get('firstname', "")
                    last_name = address.get('lastname', "")
                    exist_address_sql = frappe.db.sql("SELECT name FROM `tabAddress` WHERE custom_address_id = %s" , (address_id) , as_dict = True)
                    if exist_address_sql and exist_address_sql[0] and exist_address_sql[0]['name']:
                        address_doc = exist_address_sql[0]['name']
                    else:
                        address_doc = frappe.new_doc('Address')
                        address_doc.custom_address_id = address_id
                    address_doc.address_line1 = str(address_line)
                    counrt_id_sql = frappe.db.sql("SELECT name FROM tabCountry WHERE code = %s" , ((address['country_id']).lower()) , as_dict = True)
                    if counrt_id_sql and counrt_id_sql[0] and counrt_id_sql[0]['name']:
                        country = counrt_id_sql[0]['name']
                        address_doc.country = country
                    address_doc.state =  address['region']['region']
                    address_doc.city = city
                    address_doc.pincode = pincode
                    address_doc.phone = phone
                    address_doc.custom_first_name = first_name
                    address_doc.custom_last_name = last_name if last_name not in [None, "", '', 0, ' ', " "] else "Test"
                    address_doc.email_id = email_id 
                    if address.get('default_billing' , False): 
                        address_doc.is_primary_address = (address['default_billing'])
                    if address.get('default_shipping', False): 
                        address_doc.is_shipping_address = (address['default_shipping'])
                    customer_sql = frappe.db.sql("SELECT name FROM tabCustomer WHERE custom_customer_id = %s" , (address['customer_id']) , as_dict=True)
                    if customer_sql and customer_sql[0] and customer_sql[0]['name']:
                        customer = customer_sql[0]['name']
                        address_doc.append('links', {
                                'link_doctype': "Customer",
                                'link_name': customer
                            })
                    address_doc.save(ignore_permissions = True)
                    
                    
### Update Stock                    
def get_warehouse_code_magento():
    base_url, headers = base_data("magento")
    url = base_url + "/rest/V1/inventory/sources"
    
    response = request_with_history(
                            req_method='GET', 
                            doctype='Stock', 
                            document='Update Stock', 
                            url=url, 
                            headers=headers)
    json_response = response.json()
    if response.status_code == 200:
        return json_response
    else:
        frappe.throw(f"Error in Getting Warehouse Code. {str(response.text)}")


def get_magento_item_stock(item_code):
    base_url, headers = base_data("magento")
    url = base_url + f"/rest/V1/stockItems/{item_code}"
    response = request_with_history(
                            req_method='GET', 
                            doctype='Stock', 
                            document='Get magento Item Stock', 
                            url=url, 
                            headers=headers)
    json_response = response.json()
    if response.status_code == 200:
        return json_response
    else:
        frappe.throw(f"Error in Getting Item Stock. {str(response.text)}")

def get_qty_items_details(main , child_name , name):
    doc = frappe.qb.DocType(main)
    child = frappe.qb.DocType(child_name)
    sql = (
        frappe.qb.from_(doc).join(child).on(child.parent == doc.name)
        .where(doc.name == name)
        .groupby(child.item_code)
        .select(
            (child.item_code) , (Sum(child.qty).as_('qty'))
        )
    )
    if main == 'Stock Entry': 
        sql = sql.select((child.s_warehouse), (child.t_warehouse), (child.is_finished_item))
    return sql.run(as_dict = True)
    
               
@frappe.whitelist()
def get_customer_address(customer):
    return frappe.db.sql("""select ta.*
        from tabAddress ta 
        inner join `tabDynamic Link` tdl on tdl.parent = ta.name 
        where tdl.link_name =%s
                                """, (customer) , as_dict = True)
    
@frappe.whitelist()
def get_customer_contact(customer):
    return frappe.db.sql("""select tc.*
        from tabContact tc
        inner join `tabDynamic Link` tdl on tdl.parent = tc.name 
        where tdl.link_name  =%s
                                """, (customer) , as_dict = True)


def change_magento_status_to_fullfilled(so_name):
    base_url, headers = base_data("webhook")
    setting = frappe.get_doc("Magento Setting")
    if setting.auth_type == "Develop":
        env = "dev"
    elif setting.auth_type == "Production":
        env = "prod"
    url = base_url + '/order/updateStatus/{so_name}/{env}'.format(so_name = so_name, env = env)
    payload = json.dumps({
            "order_status": "Fulfilled"
            })
    response = request_with_history(
                            req_method='PUT', 
                            doctype='Sales Order', 
                            document=so_name, 
                            url=url, 
                            headers=headers,
                            data=payload, 
                            with_data=1)
    return response.text , response.status_code

def change_magento_status_to_cancelled(so_name , so_magento_id):
    base_url, headers = base_data("webhook")
    setting = frappe.get_doc("Magento Setting")
    if setting.auth_type == "Develop":
        env = "dev"
    elif setting.auth_type == "Production":
        env = "prod"
    url = base_url + '/order/cancel/{so_magento_id}/{env}'.format(so_magento_id = so_magento_id, env = env)
    response =  request_with_history(
                            req_method='PUT', 
                            doctype='Sales Order', 
                            document=so_name, 
                            url=url, 
                            headers=headers
                        )
    if response.status_code not in [200, 201]:
        frappe.throw(f"Failed to cancel order on Magento. Response: {response.text}")
    return response.text , response.status_code ## returns: Order (magento id) has been successfully cancelled

######## Customer Wallet Balance Magento API "Mahmoud API"
@frappe.whitelist()
def get_customer_wallet_balance(customer_id , magento_id , erpnext = True):
    if erpnext:
        balance = frappe.db.sql(""" 
            SELECT 
                IFNULL (SUM(tge.credit) - SUM(tge.debit),0 ) AS Balance
            FROM 
                `tabGL Entry` tge
            WHERE 
                tge.customer = %s
                AND tge.is_cancelled = 0 
                AND tge.party IN (SELECT name FROM `tabCustomer` WHERE custom_is_digital_wallet = 1);""",(customer_id))
        return balance[0][0] if balance else 0
    elif erpnext == False: 
        if (customer_id is not None ) and (magento_id  not in [0 , None]):
            customer_doc = frappe.get_doc('Customer' , customer_id)
            base_url, headers =base_data(request_in="magento_customer_auth" , customer_email=customer_doc.custom_email)
            url = base_url + "graphql"
            payload = {
                "query":  f"""
                    query {{
                        admincustomerwalletdetail(customerId: "{str(magento_id)}") {{
                            Amount
                            Action
                            Status
                        }}
                    }}
            """
                }
            setting = frappe.get_doc("Magento Setting")
            auth = setting.magento_admin_prod_auth
            headers['Authorization'] = f"Bearer {auth}"
            response =  request_with_history(
                                req_method='POST', 
                                doctype='Wallet Balance', 
                                document=f"for Customer:{customer_id}", 
                                url=url, 
                                headers=headers,
                                payload=payload)
            res = response.json()
            credit = 0 
            debit = 0 
            data = res.get('data')
            if data:
                wallet_details = data.get('admincustomerwalletdetail')
                if wallet_details:
                    for wd in wallet_details:
                        if wd.get('Status') == 'Approve':
                            if wd.get('Action') == 'credit':
                                credit += float(wd.get('Amount'))
                            if wd.get('Action') == 'debit':
                                debit += float(wd.get('Amount'))
            return (credit - debit)
        return None
    
    
    
def get_packed_warehouse(): 
    wh = frappe.qb.DocType('Warehouse')
    return (
        frappe.qb.from_(wh)
        .select(wh.name)
        .where(wh.custom_is_packed_wh == 1 )
        ).run(as_dict = True)
    
    
    
@frappe.whitelist()    
def customer_notification(): 
    customers = frappe.db.sql("""
                        SELECT so1.company , so1.customer ,so1.customer_name , so1.transaction_date 
                        FROM `tabSales Order` so1
                        LEFT JOIN `tabSales Order` so2 
                            ON so1.customer = so2.customer 
                            AND so2.delivery_date > so1.delivery_date
                        WHERE DATEDIFF(CURRENT_DATE() , so1.transaction_date) = 180 and so2.name IS NULL
                        GROUP BY so1.customer
                        """ , as_dict = 1 )
    for c in customers: 
        customer_email = frappe.db.get_value('Customer' , c.customer , 'custom_email')
        if customer_email is not None:
            frappe.sendmail(
                recipients=customer_email,
                subject='Last Order Notification',
                message=f"Dear {c.customer_name},<br>This is a notification that you have not placed any orders for the last 180 days.<br> Best regards,<br><b>{c.company}</b>",
                reference_doctype='Customer',
                reference_name=c.customer
            )
        
    
@frappe.whitelist()
def update_points():
    try:
        magento_id = frappe.form_dict.get("magento_id")
        if not magento_id:
            frappe.throw("Magento ID is required")

        data = frappe.form_dict.get("data")
        if not data:
            frappe.throw("Missing 'data' field in request")
        for key in data:
            if key != "custom_points_balance":
                frappe.throw(f"Invalid key '{key}' in data. Only 'custom_points_balance' is allowed.")
        if data.get("custom_points_balance") in [None, "", " "]:
            frappe.throw("Missing 'custom_points_balance' value in data")
        customer_name = frappe.get_value("Customer", {"custom_customer_id": magento_id}, "name")
        if not customer_name:
            frappe.throw(f"Customer with Magento ID {magento_id} not found")
        frappe.db.set_value("Customer", customer_name, "custom_points_balance", data["custom_points_balance"], update_modified=False)
        frappe.db.commit()

        return {
            "status": "success",
            "magento_id": magento_id,
            "message": f"Customer {customer_name} updated successfully",
            "data": data
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Update Customer by Magento ID Error")
        frappe.response["http_status_code"] = 417
        return {
            "status": "error",
            "message": str(e)
        }
        

@frappe.whitelist(methods=['POST'])
def update_address():
    try:
        magento_id = frappe.form_dict.get("magento_id")
        if not magento_id:
            frappe.throw("Magento ID is required")

        data = frappe.form_dict.get("data")
        if not data:
            frappe.throw("Missing 'data' field in request")
        
        customer_name = frappe.get_value("Customer", {"custom_customer_id": magento_id}, "name")
        if not customer_name:
            frappe.throw(f"Customer with Magento ID {magento_id} not found")
            
        customer_doc = frappe.get_doc("Customer", customer_name)
        if not customer_doc.customer_primary_address:
            frappe.throw(f"Customer {customer_name} with Magento ID {magento_id} does not have a primary address set")
            
        address_doc = frappe.get_doc("Address", customer_doc.customer_primary_address)
        if not address_doc:
            frappe.throw(f"Address for Customer ID {magento_id} not found")

        for key, value in data.items():
            if hasattr(address_doc, key):
                setattr(address_doc, key, value)
            else:
                frappe.throw(f"Invalid field '{key}' in data for Address")

        address_doc.save()
        frappe.db.commit()

        return {
            "status": "success",
            "magento_id": magento_id,
            "message": f"Address updated successfully for customer {customer_name}",
            "data": data
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Update Address by Magento ID Error")
        frappe.response["http_status_code"] = 417
        return {
            "status": "error",
            "message": str(e)
        }
        
@frappe.whitelist()
def get_address_id(customer_id, add_type):
    if not customer_id or not add_type:
        frappe.throw("Missing customer_id or address_type")

    query = frappe.db.sql("""
        SELECT 
            ta.name AS 'Address ERP ID', 
            tc.name AS 'ERP ID', 
            tc.custom_customer_id AS 'Magento ID', 
            ta.address_type AS 'Address Type',
            ta.address_title AS 'Address Title',
            ta.address_line1 AS 'Address1',
            ta.city AS 'City',
            ta.country AS 'Country',
            ta.phone AS 'Phone',
            ta.custom_first_name AS 'First Name',
            ta.custom_last_name AS 'Last Name'
        FROM 
            `tabDynamic Link` tdl
        INNER JOIN `tabCustomer` tc ON tdl.link_name = tc.name
        INNER JOIN `tabAddress` ta ON tdl.parent = ta.name
        WHERE 
            tc.custom_customer_id = %s 
            AND ta.address_type = %s
    """, (customer_id, add_type), as_dict=True)

    return query

@frappe.whitelist(methods=["POST"])
def lp_management():
    try:
        magento_id = frappe.form_dict.get("magento_id")
        if not magento_id:
            frappe.throw("Magento ID is required")

        data = frappe.form_dict.get("data")
        if not data:
            frappe.throw("Missing 'data' field in request")
        
        customer_name = frappe.get_value("Customer", {"custom_customer_id": magento_id}, "name")
        if not customer_name:
            frappe.throw(f"Customer with Magento ID {magento_id} not found")
            
        customer_doc = frappe.get_doc("Customer", customer_name)
        
        new_lpm = frappe.new_doc("Loyality Points Management")
        new_lpm.customer = customer_doc.name
        new_lpm.custom_customer_id = customer_doc.custom_customer_id
        new_lpm.customer_name = customer_doc.customer_name
        for key, value in data.items():
            if hasattr(new_lpm, key):
                setattr(new_lpm, key, value)
            else:
                frappe.throw(f"Invalid field '{key}' in data for Address")
        new_lpm.insert(ignore_permissions=True)
        new_lpm.submit()
        
        return {
            "status": "success",
            "magento_id": magento_id,
            "message": f"Loyality Points Management created successfully for customer {customer_name}",
            "data": data
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Loyality Points Management Error")
        frappe.response["http_status_code"] = 417
        return {
            "status": "error",
            "message": str(e)
        }