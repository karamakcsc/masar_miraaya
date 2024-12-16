import frappe
import requests
import os 
from masar_miraaya.api import base_data

        
def validate(self, method):
    roles = (frappe.get_roles(frappe.session.user))
    if (self.custom_is_publish and ('API Integration' not in roles)) or (self.custom_is_publish and frappe.session.user == 'Administrator' ):
        magento = frappe.get_doc('Magento Sync')
        if magento.sync == 0 :
            frappe.enqueue(
                'masar_miraaya.custom.item.item.create_new_item',
                queue='default',
                timeout=300,
                is_async=True,
                enqueue_after_commit=True,
                at_front=True,
                self = self,
            )
        else: 
            frappe.throw("Set Sync in Magento Sync disabled. To Update/Create in magento.")
def before_rename(self, method, old, new, merge):
    payload = {
        "product": {
            "id": self.custom_item_id           
        }
    }
    
    base_url, headers = base_data("magento")
    url = f"{base_url}/rest/V1/products/{new}"
    response = requests.put(url, headers=headers, json=payload)
    if response.status_code == 200:
        # json_response = response.json()
        # self.custom_item_id = json_response['id']
        # frappe.db.set_value("Item", self.name, "custom_item_id", json_response['id'])
        # frappe.db.commit()
        frappe.msgprint(f"Item Renamed Successfully in Magento" , alert=True , indicator='green')
    else:
        frappe.throw(str(f"Error Renaming Item: {str(response.text)}."))
    

def create_new_item(self):
    payload = base_item_data(self)
    base_url, headers = base_data("magento")
    url = f"{base_url}/rest/all/V1/products/{self.item_code}"
    response = requests.put(url, headers=headers, json=payload)
    if response.status_code == 200:
        json_response = response.json()
        self.custom_item_id = json_response['id']
        frappe.db.set_value("Item", self.name, "custom_item_id", json_response['id'])
        frappe.db.commit()
        frappe.msgprint(f"Item Created Successfully in Magento" , alert=True , indicator='green')
    else:
        frappe.throw(str(f"Error Creating Item: {str(response.text)}."))
    if self.variant_of:
            templete_doc = frappe.get_doc('Item' , self.variant_of)
            create_new_item(templete_doc)

        
        
        
        
def custom_attributes_function(self):
        field_mapping = {
            "brand": "brand",
            "custom_free_from": "free_from",
            "custom_key_features": "key_features",
            "custom_ingredients": "ingredients",
            "custom_how_to_use": "how_to_use",
            "custom_formulation": "formulation",
            "description": "product_description",
            # "custom_country_of_manufacture": "country_of_manufacture", 
            # "tax_class_id" : "tax_class_id",
            "custom_item_name_ar" : "arabic_name",
            "custom_arabic_metatitle":"arabic_metatitle" , 
            "custom_arabic_description":"arabic_description",
            "custom_arabic_country":"arabic_country",
            "custom_arabic_meta_keywords":"arabic_meta_keywords", 
            "custom_arabic_meta_description":"arabic_meta_description", 
            "custom_arabic_howtouse":"arabic_howtouse", 
            "custom_arabic_test_result":"arabic_testresult", 
            "custom_arabic_ingredients":"arabic_ingredients",
            "custom_article_no": "article_no", 
            "custom_meta_title":"meta_title",
            "custom_meta_keyword" :"meta_keyword",
            "custom_meta_description":"meta_description",
            "custom_warning_quantity":"warning_quantity"
        }
        country_id = None
        country_id_sql = frappe.db.sql("SELECT code FROM tabCountry WHERE name = %s" , (self.custom_country_of_manufacture) , as_dict = True)
        if country_id_sql and country_id_sql[0] and country_id_sql[0]['code']:
            country_id = country_id_sql[0]['code']
            
            
        custom_attributes = list()
        for k , v in field_mapping.items():
            attribute_code = v
            value = getattr(self, k, None)
            custom_attributes.append(frappe._dict({
                'attribute_code' : attribute_code , 
                'value' :value
            }))
            
        if country_id is not None:
            custom_attributes.append(frappe._dict({
                'attribute_code': 'country_of_manufacture',
                'value': country_id.upper()
            }))
        else:
            custom_attributes.append(frappe._dict({
                'attribute_code': 'country_of_manufacture',
                'value': None
            }))
        
        
        custom_attributes.append(frappe._dict({
                'attribute_code': 'tax_class_id',
                'value': 2
            }))
        
        custom_attributes.append({
            "attribute_code": "url_key",
            "value": f"{self.item_name.lower()}-{self.item_code.lower()}"
        })
        
        if len(self.attributes) != 0 :
            for attributes in self.attributes: 
                if self.has_variants:
                    att_doc = frappe.get_doc('Item Attribute' , attributes.attribute)
                    abbr = {
                        "Color": 93,
                        "shade": 159,
                        "Size": 144,
                        "Size (ml)": 158
                    }.get(attributes.attribute)
                    custom_attributes.append ({'attribute_code' :att_doc.custom_attribute_code ,
                                            'value' : str(abbr)})
            
                else:
                    
                    att_doc = frappe.get_doc('Item Attribute' , attributes.attribute)
                    abbr = frappe.db.sql('SELECT abbr FROM `tabItem Attribute Value` WHERE parent = %s and attribute_value = %s' ,( attributes.attribute ,attributes.attribute_value ) )[0][0]
                    custom_attributes.append ({'attribute_code' :att_doc.custom_attribute_code ,
                                            'value' : abbr})
        # if self.image:
        #     custom_images = ['image' , 'small_image' , 'thumbnail' , 'swatch_image']
        #     path_image = self.image
        #     image_name = os.path.basename(path_image)
        #     custom_attributes.append 
        #     for image in custom_images:
        #         custom_attributes.append ({'attribute_code' :image , 'value' : str(image_name)})
        return custom_attributes
            
def attribute_set_id_function(self): 
    #########################################################
    return 16 

def price_function(self): 
    price = get_item_price(self.item_code, self.stock_uom)
    if price in [ None , 0 ]:
        return 0 
    return price

def product_links_function(self):
    links = frappe.db.sql("""
                        SELECT tia.alternative_item_code 
                        FROM `tabItem Alternative` tia
                        WHERE tia.item_code = %s  AND tia.custom_is_publish =1 """ , (self.name) , as_dict=True)
    product_links = list()
    if len(links) == 0 :
        return product_links
    else:
        for link in links:
            sku = self.name 
            link_type = "related"
            linked_product_type =  "simple"
            position = 0
            linked_product_sku = link.alternative_item_code
            product_links.append(frappe._dict(
                {
                    'sku' : sku , 
                    'link_type' : link_type , 
                    'linked_product_sku' : linked_product_sku , 
                    'linked_product_type' : linked_product_type , 
                    'position' : position
                }
                )
            )
        return product_links

@frappe.whitelist()
def base_item_data(self):
        sku = self.item_code
        name = self.item_name
        visibility = {
            'Not Visible Individually': 1,
            'Catalog': 2,
            'Search': 3,
            'Catalog & Search': 4
        }.get(self.custom_visibility, 4)
        item_group_ids = get_item_groups(self.item_group)
        category_links = [
            {"position": idx, "category_id": id}
            for idx, id in enumerate(item_group_ids)
        ]
        brand_id = get_brand_id(self.brand)
        if brand_id:  ## To Add Brand in Category
            category_links.append({"position": len(item_group_ids), "category_id": brand_id})
        # frappe.throw(str(category_links))
        extension_attributes =  {
                    "website_ids": [
                        1
                    ],
                    "category_links": category_links
                }
        if self.has_variants:
            type_id = "configurable"
            product_options = list()
            if self.attributes:
                position =0 
                for attribute in self.attributes:
                    label = attribute.attribute
                    attribute_id = {
                        "Color": 93,
                        "shade": 159,
                        "Size": 144,
                        "Size (ml)": 158
                    }.get(label)
                    values_sql = frappe.db.sql("""
                                            SELECT parent, abbr FROM `tabItem Attribute Value` tiav 
                                            WHERE parent = %s AND abbr REGEXP '^[0-9]+$'""" ,(label)  , as_dict = True )
                    values_list = list()
                    for value in values_sql: 
                        values_list.append(frappe._dict(
                            {
                                "value_index": int(value.abbr)
                            }
                        ))
                    attributes_data = {
                        'attribute_id' : attribute_id ,
                        'label' : label ,
                        'position' : position , 
                        'values' : values_list 
                    }
                    position+=1
                    product_options.append(attributes_data)
            configurable_product_links = list()
            vairant_of_sql = frappe.db.sql("SELECT name , custom_item_id FROM tabItem ti WHERE variant_of  =  %s AND custom_is_publish = 1 " , self.name  , as_dict = True)
            if len(vairant_of_sql) != 0 :
                for product in vairant_of_sql:
                    if int(product.custom_item_id) !=0:
                        configurable_product_links.append(int(product.custom_item_id))
            extension_attributes["configurable_product_options"] = product_options
            extension_attributes["configurable_product_links"] = configurable_product_links                       
        else:
            type_id = "simple"
        attribute_set_id = attribute_set_id_function(self)
        price =  price_function(self)
        if self.disabled == 0 :
            status = 1
        else:
            status = 2 
        product_links = product_links_function(self)
        custom_attributes = custom_attributes_function(self)
        json_data = frappe._dict({
            "product": {
            'sku' : sku , 
            'name' : name , 
            'attribute_set_id' : attribute_set_id , 
            'price' : price,
            'status' :status , 
            'visibility' : visibility , 
            'type_id' :type_id ,
            'extension_attributes' : extension_attributes, 
            'product_links' : product_links,
            'options': [], 
            'custom_attributes': custom_attributes
            }
        })   
        return json_data
    
@frappe.whitelist()
def get_actual_qty_value(item_code):
    warehouse = frappe.db.get_value(
        'Item Default',
        {'parent': item_code},
        'default_warehouse'
    )
    item_actual_qty = frappe.db.sql("""
        SELECT actual_qty 
        FROM `tabBin` 
        WHERE item_code = %s AND warehouse = %s
    """, (item_code, warehouse), as_dict=True)
    
    if item_actual_qty:
        actual_qty = item_actual_qty[0].get('actual_qty', 0)
    else:
        actual_qty = 0
    return actual_qty

@frappe.whitelist()
def get_item_price(item_code, uom):
    item_price = frappe.db.sql(""" SELECT price_list_rate FROM `tabItem Price` 
                                    WHERE item_code = %s AND uom = %s """, (item_code, uom), as_dict = True)
    price = item_price[0]['price_list_rate'] if item_price and item_price[0].get('price_list_rate') else 0
    
    return price

@frappe.whitelist()
def get_item_groups(item_group, item_groups_ids=None):
    if item_groups_ids is None:
        item_groups_ids = []
    
    item_group_query = frappe.db.sql("""
        SELECT tig.custom_item_group_id, tig.parent_item_group 
        FROM `tabItem Group` tig 
        WHERE tig.item_group_name = %s
    """, (item_group), as_dict=True)
    
    if item_group_query:
        item_groups_ids.append(item_group_query[0]['custom_item_group_id'])
        
        parent_item_group = item_group_query[0]['parent_item_group']
        
        if parent_item_group and parent_item_group != '1 - Root Catalog':
            return get_item_groups(parent_item_group, item_groups_ids)
    
    return item_groups_ids


def get_brand_id(brand):    ## To Get Brand Id
    brand_query = frappe.db.sql(f"""
        SELECT tig.custom_item_group_id
        FROM `tabItem Group` tig 
        WHERE tig.item_group_name LIKE "%{brand}%"
    """,  as_dict=True)
    brand_id = None
    if brand_query:
        brand_id = brand_query[0]['custom_item_group_id']
                    
    return brand_id