
import frappe 
from erpnext import get_default_currency
import requests
from io import BytesIO
import base64
from urllib.parse import urlparse



def validate_url(url):
    base_url , headers = base_request_magento_data()
    parsed_url = urlparse(url)
    if not parsed_url.scheme:
        url = f"{base_url}/media/catalog/product" + url
    return url
def base_request_data():
    setting = frappe.get_doc("Magento Setting")
    base_url = str(setting.frappe_url).strip()
    headers = {
        "Authorization": f"Basic {str(setting.frappe_auth).strip()}",
        "Content-Type": "application/json"
    }
    return base_url , headers
##########################################################################
def base_request_magento_data():
    setting = frappe.get_doc("Magento Setting")
    base_url = str(setting.magento_url).strip()
    headers = {
        "Authorization": f"Bearer {str(setting.magento_auth).strip()}",
        "Content-Type": "application/json"
    }
    return base_url , headers

@frappe.whitelist()
def get_magento_item_attribute(all_items , all_configurable , altenative_items):
    try:
        frappe.enqueue(
            'masar_miraaya.api_tools.get_magento_item_attributes_in_enqueue',
            queue='long',
            timeout=5000,
            is_async=True,
            enqueue_after_commit=True,
            at_front=True,
            all_items = all_items , 
            all_configurable = all_configurable , 
            altenative_items = altenative_items
        )
    except Exception as ex:
        return f"Error While Sync with Brand {str(ex)}"

def get_magento_item_attributes_in_enqueue(all_items , all_configurable , altenative_items):
    base_url, headers = base_request_magento_data()
    try:
        url = base_url + "/rest/V1/products/attributes?searchCriteria[pageSize]=100"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        json_response = response.json()
        attributes = json_response['items']
        print("_______________________________________________________________")
        print(json_response)
        # attributes = [attr for attr in json_response['items'] if attr['attribute_code'] in ['color', 'size_ml', 'shade', 'size']]
        for attribute in attributes:
            process_item_attribute(attribute)
            # process_item_attribute(attribute['default_frontend_label'], attribute['options'],attribute['attribute_code'] ) 
        # return "Success"
    except requests.exceptions.RequestException as e:
        return f"Error getting Magento colors: {e}"
    except Exception as e:
        return f"Error processing Magento colors: {e}"
    try:
        frappe.enqueue(
            'masar_miraaya.api_tools.create_templete_items',
            queue='long',
            timeout=5000,
            is_async=True,
            enqueue_after_commit=True,
            at_front=True,
            all_items=all_items ,
            all_configurable = all_configurable,
            altenative_items = altenative_items
        )
    except Exception as ex:
        return f"Error while Create Item Templete {str(ex)}"
    

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

    
################### From Mahmoud 
############# To Sync with Item Group 
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
    try:
        magento_categories = get_magento_categories()
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
###################### Check Item Group 
@frappe.whitelist()
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
            return item_group_sql[0]['name'] if item_group_sql and item_group_sql[0] else None     
    except Exception as ex:
        return (f"Error in get_item_group_by_item_group_id: {str(ex)}")
######################################################################### 
############### To Sync to Brand 
@frappe.whitelist()
def get_magento_brand(response_json):
    try:
        create_item_group()
    except Exception as ex : 
        return "Exception Sync Item Group from Brands :" + str(ex) 
    try:
        base_url_frappe, headers_frappe = base_request_data()
        brands = frappe.db.sql("""SELECT item_group_name FROM `tabItem Group` tig WHERE custom_parent_item_group_id = '404' """, as_dict = True)
        for brand in brands:
            
            brand_name = brand['item_group_name'].split(' - ', 1)[-1].strip()
            exist_brands = frappe.db.sql("""SELECT name FROM `tabBrand` WHERE name = %s""" , (brand_name) , as_dict = 1 )
            if not (exist_brands and exist_brands[0] and exist_brands[0]['name']): 
                payload = {
                    "doctype": "Brand",
                    "brand": brand_name
                }
                response = requests.post(f"{base_url_frappe}/Brand", headers=headers_frappe, json=payload)
                response.raise_for_status()
        # return "Sync Brand and Item Group Completed Successfully"
    except Exception as e:
        return (f"General Error: {e}", "Magento Sync")
    
    all_items = response_json['items']
    all_configurable = list()
    altenative_items = list()
    for configurable in all_items:
        if configurable['type_id'] == "configurable":
            templete_code = configurable['sku']
            templete_id = configurable['id']
            links_product = configurable['extension_attributes']['configurable_product_links']
            all_configurable.append(frappe._dict(
                        {
                        'templete_code' : templete_code, 
                        'templete_id' : templete_id,
                        'links_product' : links_product
                        }
                    )
                )
        if len(configurable["product_links"]) !=0:
            altenative_items.append(frappe._dict({'links_product' : configurable["product_links"], }))
    try:
        get_magento_item_attribute_(all_items , all_configurable ,altenative_items )
    except Exception as ex:
        return f"Error while Sync in Item Attribute : {str(ex)}"
    
def get_magento_item_attribute_(all_items , all_configurable ,altenative_items ):
        get_magento_item_attribute(all_items , all_configurable ,altenative_items )


############################################################################
############ To Add Item images 
@frappe.whitelist()
def upload_image_to_item( file ,  item_code , base_image):
    try:
        image_url = validate_url(file)
        response = requests.get(image_url)
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

##################################################
###################### To Sync with item 
@frappe.whitelist()
def get_magento_products_json():
        base_url, headers = base_request_magento_data()
        url = base_url + "/rest/V1/products?searchCriteria="
        request = requests.get(url, headers=headers)
        json_response = request.json()
        return json_response

@frappe.whitelist()
def get_magento_products():
    try: 
        response_json = get_magento_products_json()
    except Exception as ex:
        return f"Error in Magento Connection : {str(ex)}"
    ####### Chech for Brand And Item Group 
    try:
        frappe.enqueue(
            'masar_miraaya.api_tools.get_magento_brand',
            queue='long',
            timeout=5000,
            is_async=True,
            enqueue_after_commit=True,
            at_front=True,
            response_json =response_json
        )
    except Exception as ex:
        return f"Error While Sync with Brand {str(ex)}"
    

     ### get varint items to build templete 
def create_templete_items(all_items , all_configurable , altenative_items):
    for configurable in all_items:
        if configurable['type_id'] == "configurable":
            category_id_max = 0 
            exist_templete = frappe.db.sql("SELECT name FROM `tabItem` WHERE item_code = %s" ,(configurable['sku']) , as_dict=True)
            if not(exist_templete and exist_templete[0] and exist_templete[0]['name']):
                templete_code = configurable['sku']
                templete_id = configurable['id']
                templete_name = configurable['name']
                if configurable['status'] == 1:
                    publish_to_magento = 1 
                    disabled = 0 
                elif configurable['status'] == 2:
                    publish_to_magento = 0
                    disabled = 1 
                visibility_mapping = {
                        1: 'Not Visible Individually',
                        2: 'Catalog',
                        3: 'Search',
                        4: 'Catalog & Search'
                    }
                visibility = visibility_mapping.get(configurable['visibility'], '')
                if configurable['extension_attributes'] and configurable['extension_attributes']['category_links']:
                    category_links = configurable['extension_attributes']['category_links']
                    for cat_id in category_links:
                            category_id = int(cat_id['category_id'])
                            if category_id_max == 0 or category_id > category_id_max:
                                    category_id_max = category_id
                if  category_id_max :
                        item_group = get_item_group_by_item_group_id(category_id_max)
                has_variants = 1 
                ############# Create a Templete 
                new_templete = frappe.new_doc('Item')
                new_templete.item_code = templete_code
                new_templete.item_name = templete_name
                new_templete.custom_item_id = templete_id
                new_templete.item_group = item_group
                new_templete.custom_visibility = visibility
                new_templete.custom_magento_item_type = "configurable"
                new_templete.insert(ignore_permissions=True)
                frappe.db.set_value('Item' ,new_templete.name , 'has_variants' , has_variants )
                
                print(f"Item Group: {item_group}")
                configurable_options  = configurable['extension_attributes']['configurable_product_options']
                if len(configurable_options) !=0 :
                    for options in configurable_options:
                        attributes = frappe.new_doc("Item Variant Attribute")
                        attributes.attribute =  str(options['label'])
                        attributes.parentfield = 'attributes'
                        attributes.parenttype = 'Item'
                        attributes.parent = new_templete.name
                        attributes.insert(ignore_permissions=True)
                frappe.db.set_value('Item' ,new_templete.name , 'custom_is_publish' , publish_to_magento )
                frappe.db.set_value('Item' ,new_templete.name , 'disabled' , disabled )
                for custom_attributes in configurable['custom_attributes']:
                    att_code =custom_attributes['attribute_code']
                    att_value = custom_attributes['value']
                    if att_code == "brand":
                        brand_sql = frappe.db.sql("SELECT name FROM `tabBrand` WHERE name = %s" , (att_value) , as_dict = True)
                        if brand_sql and brand_sql[0] and brand_sql[0]['name']:
                            brand = brand_sql[0]['name']
                        else:
                            new_brand = frappe.new_doc('Brand')
                            new_brand.brand = att_value
                            new_brand.insert(ignore_permissions=True)
                            brand = new_brand.name
                        new_templete.brand = brand
                        frappe.db.set_value('Item' ,new_templete.name , 'brand' , brand )
                    if att_code == "free_from":
                        if att_value not in [ None , ""]:
                            frappe.db.set_value('Item' ,new_templete.name , 'custom_free_from' , att_value )
                    if att_code == "key_features":
                        if att_value not in [ None , ""]:
                            frappe.db.set_value('Item' ,new_templete.name , 'custom_key_features' , att_value )
                    if att_code == "ingredients":
                        if att_value not in [ None , ""]:
                            frappe.db.set_value('Item' ,new_templete.name , 'custom_ingredients' , att_value )
                    if att_code == "how_to_use":
                        if att_value not in [ None , ""]:
                            frappe.db.set_value('Item' ,new_templete.name , 'custom_how_to_use' , att_value )
                    if att_code == "formulation":
                        if att_value not in [ None , ""]:
                            frappe.db.set_value('Item' ,new_templete.name , 'custom_formulation' , att_value )
                    if att_code == "product_description":
                        if att_value not in [ None , ""]:
                            frappe.db.set_value('Item' ,new_templete.name , 'description' , att_value )
                    if att_code == "country_of_manufacture":
                        if att_value not in [ None , ""]:
                            frappe.db.set_value('Item' ,new_templete.name , 'custom_country_of_manufacture' , att_value )
                # try:
                #         for media in configurable['media_gallery_entries']:
                #             if media['media_type'] ==  "image":
                #                 if len(media['types']) !=0 : 
                #                     base_image = 1 
                #                 else:
                #                     base_image = 0 
                #                 url_file  = upload_image_to_item(
                #                                         file=media['file'], 
                #                                         item_code= templete_code,
                #                                         base_image = base_image
                #                                         )
                #                 if url_file :
                #                     frappe.db.set_value('Item' ,new_templete.name , 'image' , url_file )
                # except Exception as ex:
                #         return f"Error While upload Images to item "+ str(ex)
    get_magento_products_in_enqueue_(all_items,all_configurable ,altenative_items)


def get_magento_products_in_enqueue_(all_items ,all_configurable  ,altenative_items):
    batch_size = 100
    total_items = len(all_items)
    final_loop = False
    for i in range(0, len(all_items), batch_size):
        if i + batch_size >= total_items:
            final_loop = True
        batch = all_items[i:i + batch_size]
        frappe.enqueue(
            'masar_miraaya.api_tools.get_magento_products_in_enqueue',
            queue='long',
            timeout=5000,
            is_async=True,
            enqueue_after_commit=True,
            at_front=True,
            response_json={'items': batch} , 
            all_configurable= all_configurable , 
            final_loop = final_loop ,
            altenative_items = altenative_items
        )
    


    return f"Done"


def get_magento_products_in_enqueue(response_json, all_configurable, final_loop, altenative_items):
    try:
        all_items = response_json['items']
        for item in all_items:
            if item['type_id'] == "simple":
                # Initialize necessary variables and fetch existing item details
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
                    
                    # Category processing
                    if item['extension_attributes'] and item['extension_attributes']['category_links']:
                        category_links = item['extension_attributes']['category_links']
                        for cat_id in category_links:
                            category_id = int(cat_id['category_id'])
                            if category_id_max == 0 or category_id > category_id_max:
                                category_id_max = category_id
                    if category_id_max:
                        item_group = get_item_group_by_item_group_id(category_id_max)
                    
                    # Status processing
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
                    frappe.db.set_value('Item', new_item_.name, 'disabled', disabled)
                    
                    # Variant processing
                    for configurable in all_configurable:
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
                        if att_code == "country_of_manufacture" and att_value:
                            frappe.db.set_value('Item', new_item_.name, 'custom_country_of_manufacture', att_value)

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
                    # try:

                    #     for media in item['media_gallery_entries']:
                    #         if media['media_type'] == "image":
                    #             base_image = 1 if media['types'] else 0
                    #             url_file = upload_image_to_item(
                    #                 file=media['file'], 
                    #                 item_code=item_code,
                    #                 base_image=base_image
                    #             )
                    #             if url_file:
                    #                 frappe.db.set_value('Item', new_item_.name, 'image', url_file)
                    # except Exception as ex:
                    #     return f"Error While uploading Images to item: {str(ex)}"
                    
                    insert_item_price(
                            item_code=new_item_.name ,
                            uom = new_item_.stock_uom , 
                            item_name=item_name ,
                            brand = brand,
                            rate = str(rate)
                        )  
                    frappe.db.commit()  # Ensure all operations are committed

        if final_loop and altenative_items:
            frappe.enqueue(
                'masar_miraaya.api_tools.get_alternative_items',
                queue='long',
                timeout=5000,
                is_async=True,
                enqueue_after_commit=True,
                at_front=True,
                altenative_items=altenative_items
            )

    except Exception as ex:
        return f"Exception in get_magento_products: {str(ex)}"
############################## Inset Item Price 
def insert_item_price(
        item_code ,
        item_name ,
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
    # item_price = frappe.new_doc('Item Price')
    # item_price.item_code = item_code
    # item_price.item_name = item_name
    # item_price.price_list = price_list
    # item_price.uom = uom
    # item_price.brand = brand
    # item_price.rate =float(rate)
    # item_price.insert(ignore_permissions=True , ignore_mandatory=True)
####################################### Insert Item Alternative 
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
                
                
                
                
                
                
                
                
########################33

def process_item_attribute(attribute):
    try:
        if frappe.db.exists('Attributes', attribute['default_frontend_label']):
            new_attribute = frappe.get_doc('Attributes',  attribute['default_frontend_label'])
        else:
            new_attribute = frappe.new_doc('Attributes')
            new_attribute.default_frontend_label =  attribute['default_frontend_label']
            new_attribute.is_wysiwyg_enabled =  attribute['is_wysiwyg_enabled']
            new_attribute.is_html_allowed_on_front =  attribute['is_html_allowed_on_front']
            new_attribute.used_for_sort_by =  attribute['used_for_sort_by']
            new_attribute.is_filterable =  attribute['is_filterable']
            new_attribute.is_filterable_in_search =  attribute['is_filterable_in_search']
            new_attribute.is_used_in_grid =  attribute['is_used_in_grid']
            new_attribute.is_visible_in_grid =  attribute['is_visible_in_grid']
            new_attribute.is_filterable_in_grid =  attribute['is_filterable_in_grid']
            new_attribute.apply_to =  str(attribute['apply_to'])
            new_attribute.is_searchable =  attribute['is_searchable']
            new_attribute.is_visible_in_advanced_search =  attribute['is_visible_in_advanced_search']
            new_attribute.is_comparable =  attribute['is_comparable']
            new_attribute.is_used_for_promo_rules =  attribute['is_used_for_promo_rules']
            new_attribute.is_visible_on_front =  attribute['is_visible_on_front']
            new_attribute.used_in_product_listing =  attribute['used_in_product_listing']
            new_attribute.scope =  attribute['scope']
            new_attribute.is_visible =  attribute['is_visible']
            new_attribute.attribute_code =  attribute['attribute_code']
            new_attribute.is_required =  attribute['is_required']
            new_attribute.default_value =  attribute['default_value']
            if attribute['default_value']:
                new_attribute.append('att_details' , {
                    'label' : 'Default', 'value': attribute['default_value']
                })
            for option in attribute['options']:
                    if (option['value'] not in [None, "", '', 0, ' ', " "]) and (option['label'] not in [None, "", '', 0, " ", ' ']):
                            existing_attribute_value = frappe.db.get_value('Attributes Details', {
                                'parent': attribute['default_frontend_label'],
                                'label': str(option['label'])
                            }, 'name')
                            if not existing_attribute_value:
                                new_attribute.append('att_details' , {
                                    'label' : option['label'],
                                    'value': option['value']
                                })

            new_attribute.insert(ignore_permissions=True)
            apply_done = False
            for apply in attribute['apply_to']:
                if apply in ['simple', 'virtual', 'downloadable', 'bundle', 'configurable'] and apply_done ==False:
                    if frappe.db.exists('Item Attribute', attribute['default_frontend_label']):
                        item_attribute = frappe.get_doc('Item Attribute',  attribute['default_frontend_label'])
                    else:
                        item_attribute = frappe.new_doc('Item Attribute')
                        item_attribute.attribute_name =  attribute['default_frontend_label']
                        item_attribute.custom_attribute_code =  attribute['attribute_code']
                        item_attribute.insert(ignore_permissions=True)
                    
                    for option in attribute['options']:
                        if (option['value'] not in [None, "", '', 0, ' ', " "]) and (option['label'] not in [None, "", '', 0, " ", ' ']):
                            existing_attribute_value = frappe.db.get_value('Item Attribute Value', {
                                'parent': attribute['default_frontend_label'],
                                'attribute_value': str(option['label'])
                            }, 'name')
                            if not existing_attribute_value:
                                new_attribute_value = frappe.new_doc('Item Attribute Value')
                                new_attribute_value.attribute_value = str(option['label'])
                                new_attribute_value.abbr = str(option['value'])
                                new_attribute_value.parent = attribute['default_frontend_label']
                                new_attribute_value.parentfield = 'item_attribute_values'
                                new_attribute_value.parenttype = 'Item Attribute'
                                new_attribute_value.insert(ignore_permissions=True)
                                apply_done = True
    except frappe.DatabaseError as e:
        return f"Error processing attribute {attribute['default_frontend_label']}: {e}"
    except Exception as e:
        return f"Error processing attribute {attribute['default_frontend_label']}: {e}"