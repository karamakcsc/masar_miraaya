# import frappe
# import requests
# from masar_miraaya.api import base_data

        
# def validate(self, method):
#     pass
#     if self.custom_is_publish and not self.variant_of:
#         magento = frappe.get_doc('Magento Sync')
#         if magento.sync == 0 :
#             create_new_item(self)
#         else: 
#             frappe.throw("Set Sync in Magento Sync disabled. To Update/Create in magento.")
    

# def on_update(self, method):
#     if self.custom_is_publish and self.variant_of:
#         magento = frappe.get_doc('Magento Sync')
#         if magento.sync == 0 :
#             create_new_item(self)
#         else: 
#             frappe.throw("Set Sync in Magento Sync disabled. To Update/Create in magento.")


# @frappe.whitelist()
# def create_new_item(self):
#     try:
        # base_url, headers = base_data("magento")
        # url = f"{base_url}/rest/V1/products/{self.item_code}"

#         is_active = 2 if self.disabled else 1 #### 1 Enabled, 2 Disabled ############# 3 Out of Stock (not tested)
        
#         visibility = {
#             'Not Visible Individually': 1,
#             'Catalog': 2,
#             'Search': 3,
#             'Catalog, Search': 4
#         }.get(self.custom_visibility, 4)

#         ean = None
#         if self.barcodes:
#             for barcode in self.barcodes:
#                 ean = barcode.barcode
#                 break
        
#         item_group_ids = get_item_groups(self.item_group)
#         category_links = [
#             {"position": idx, "category_id": id}
#             for idx, id in enumerate(item_group_ids)
#         ]
        
#         ######### get the value for custom attributes (color, shade, size, size_ml)
#         attribute_query = frappe.db.sql(""" SELECT DISTINCT tiav.parent, tiav.attribute_value , tiav.abbr
#                                             FROM `tabItem Attribute Value` tiav
#                                             INNER JOIN `tabItem Variant Attribute` tiva ON tiav.attribute_value = tiva.attribute_value 
#                                             INNER JOIN `tabItem` ti ON ti.name = tiva.parent 
#                                             WHERE ti.name = %s and tiva.attribute = tiav.parent
#                                          """, (self.item_code), as_dict = True)
#         size_abbr = 0
#         size_ml_abbr = 0
#         color_abbr = 0
#         shade_abbr = 0
#         for data in attribute_query:
#             if data['parent'].lower() == 'size':
#                 size_abbr = data['abbr']
#             elif data['parent'].lower() == 'size (ml)':
#                 size_ml_abbr = data['abbr']
#             elif data['parent'].lower() == 'color':
#                 color_abbr = data['abbr']
#             elif data['parent'].lower() == 'shade':
#                 shade_abbr = data['abbr']
        
#         # frappe.throw(str(color_abbr))        
        
#         product_type = "configurable" if self.has_variants else "simple"
        
#         ######### base data payload
#         data = {
#             "product": {
#                 "sku": self.name,
#                 "name": self.item_name,
#                 "price": get_item_price(self.item_code, self.stock_uom),
#                 "status": is_active,
#                 "visibility": visibility,
#                 "type_id": product_type,
#                 "attribute_set_id": 16,
#                 "extension_attributes": {
#                     "website_ids": [1],
#                     "category_links": category_links
#                 },
#             }
#         }
        
#         ######### add custom attributes
#         custom_attributes_dict = {}
#         if self.brand:
#             custom_attributes_dict["brand"] = self.brand
#         if self.custom_free_from:
#             custom_attributes_dict["free_from"] = self.custom_free_from
#         if self.custom_key_features:
#             custom_attributes_dict["key_features"] = self.custom_key_features
#         custom_attributes_dict["url_key"] = f"{self.name}-{self.item_name}" if self.item_name else self.name
#         if self.custom_ingredients:
#             custom_attributes_dict["ingredients"] = self.custom_ingredients
#         if ean:
#             custom_attributes_dict["ean"] = ean
#         if self.custom_how_to_use:
#             custom_attributes_dict["how_to_use"] = self.custom_how_to_use
#         if self.custom_item_name_ar:
#             custom_attributes_dict["arabic_name"] = self.custom_item_name_ar
#         if self.custom_formulation:
#             custom_attributes_dict["formulation"] = self.custom_formulation
#         if self.description:
#             custom_attributes_dict["product_description"] = str(self.description)
#         if self.custom_country_of_manufacture:
#             custom_attributes_dict["country_of_manufacture"] = self.custom_country_of_manufacture
#         if shade_abbr:
#             custom_attributes_dict["shade"] = shade_abbr if shade_abbr else 0
#         if size_ml_abbr:
#             custom_attributes_dict["size_ml"] = size_ml_abbr if size_ml_abbr else 0
#         if size_abbr:
#             custom_attributes_dict["size"] = size_abbr if size_abbr else 0
#         if color_abbr:
#             custom_attributes_dict["color"] = color_abbr if color_abbr else 0
        
#         ########## Static Custom Attributes
#         custom_attributes_dict["options_container"] = "container2"
#         custom_attributes_dict["tax_class_id"] = "2"

#         custom_attributes = [
#             {
#                 "attribute_code": key,
#                 "value": value
#             } for key, value in custom_attributes_dict.items()
#         ]
        
#         ######### add custom attributes to payload
#         if custom_attributes:    
#             data["product"]["custom_attributes"] = custom_attributes
        
#         ######### if item is template
#         if self.has_variants:
#             product_options = []
#             if self.attributes:
#                 for attribute in self.attributes:
#                     attribute_name = attribute.attribute.lower().title()
#                     attribute_id_map = {
#                         "Color": 93,
#                         "Shade": 159,
#                         "Size": 144,
#                         "Size (ml)": 158
#                     }.get(attribute_name)
                    
#                     if attribute_id_map:
#                         values_sql = frappe.db.sql('SELECT abbr FROM `tabItem Attribute Value` WHERE LOWER(parent) = %s AND attribute_value != "Default"', (attribute_name.lower()), as_dict=True)
#                         values = [{"value_index": int(value.abbr)} for value in values_sql]
                        
#                         option = {
#                             'attribute_id': attribute_id_map, 
#                             'label': attribute.attribute, 
#                             'values': values
#                         }
#                         product_options.append(option)
                
#             # frappe.throw(str(product_options))
#             data["product"]["extension_attributes"]["configurable_product_options"] = product_options
            
#             ######### add product links
#             variant_item_ids = [item['custom_item_id'] for item in frappe.db.sql("""
#                                             SELECT ti.custom_item_id
#                                             FROM tabItem ti 
#                                             WHERE ti.variant_of = %s
#                                             """, (self.name), as_dict=True)]
#             data["product"]["extension_attributes"]["configurable_product_links"] = variant_item_ids
#             # frappe.throw(str(variant_item_ids))
            
#         # frappe.throw(str(data))
#         response = requests.put(url, headers=headers, json=data)
#         if response.status_code == 200:
#             json_response = response.json()
#             frappe.db.set_value('Item', json_response['sku'], 'custom_item_id', json_response['id'])
#             frappe.db.commit()
            # if self.variant_of:     ####### Save the template item for effect on magento
            #     template_doc = frappe.get_doc("Item", self.variant_of)
            #     template_doc.save(ignore_permissions=True)
#             if self.has_variants:           #### to set the item id for all variants (needs testing)
#                 for item in json_response:
#                     frappe.db.set_value('Item', item['sku'], 'custom_item_id', item['id'])
#                     frappe.db.commit()
#             frappe.msgprint(f"Item Created Successfully in Magento" , alert=True , indicator='green')
#         else:
#             frappe.throw(f"Failed to Create or Update Item in Magento: {str(response.text)}")
#     except requests.RequestException as e:
#         frappe.throw(f"Failed to Create or Update Item in Magento: {str(e)}")

# @frappe.whitelist()
# def remove_image_from_magento(self, entity_id):
#     base_url, headers = base_data("magento")
#     try:
#         url = base_url + f"/rest/V1/products/{self.item_code}/media/{entity_id}"
        
#         response = requests.delete(url, headers=headers)
        
#         if response.status_code == 200:
#             frappe.msgprint("Image Deleted Successfully From Magento")
#         else:
#             frappe.throw(f"Error Deleting Image: {response.text}")
            
#     except Exception as e:
#         frappe.throw(str(f"Error Removing Image from Magento: {e}"))

# @frappe.whitelist()
# def get_item_price(item_code, uom):
#     item_price = frappe.db.sql(""" SELECT price_list_rate FROM `tabItem Price` 
#                                     WHERE item_code = %s AND uom = %s """, (item_code, uom), as_dict = True)
#     price = item_price[0]['price_list_rate'] if item_price and item_price[0].get('price_list_rate') else 0
    
#     return price

# @frappe.whitelist()
# def get_item_groups(item_group, item_groups_ids=None):
#     if item_groups_ids is None:
#         item_groups_ids = []
    
#     item_group_query = frappe.db.sql("""
#         SELECT tig.custom_item_group_id, tig.parent_item_group 
#         FROM `tabItem Group` tig 
#         WHERE tig.item_group_name = %s
#     """, (item_group), as_dict=True)
    
#     if item_group_query:
#         item_groups_ids.append(item_group_query[0]['custom_item_group_id'])
        
#         parent_item_group = item_group_query[0]['parent_item_group']
        
#         if parent_item_group and parent_item_group != '1 - Root Catalog':
#             return get_item_groups(parent_item_group, item_groups_ids)
    
#     return item_groups_ids

# @frappe.whitelist()
# def get_values(item_code):
#     warehouse = frappe.db.get_value(
#         'Item Default',
#         {'parent': item_code},
#         'default_warehouse'
#     )
#     item_actual_qty = frappe.db.sql("""
#         SELECT actual_qty 
#         FROM `tabBin` 
#         WHERE item_code = %s AND warehouse = %s
#     """, (item_code, warehouse), as_dict=True)
    
#     if item_actual_qty:
#         actual_qty = item_actual_qty[0].get('actual_qty', 0)
#     else:
#         actual_qty = 0

#     return actual_qty



#######################################################################################################3
import frappe
import requests
import os 
from masar_miraaya.api import base_data

        
def validate(self, method):
    if self.custom_is_publish:
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
                # variant_of = self.variant_of if self.variant_of else None
            ) 
        else: 
            frappe.throw("Set Sync in Magento Sync disabled. To Update/Create in magento.")


def create_new_item(self, variant_of=None):
    # self = frappe.get_doc("Item", name)
    payload = base_item_data(self)
    base_url, headers = base_data("magento")
    url = f"{base_url}/rest/V1/products/{self.item_code}"
    response = requests.put(url, headers=headers, json=payload)
    if response.status_code == 200:
        json_response = response.json()
        self.custom_item_id = json_response['id']
        frappe.db.set_value("Item", self.name, "custom_item_id", json_response['id'])
        frappe.db.commit()
        frappe.msgprint(f"Item Created Successfully in Magento" , alert=True , indicator='green')
        if variant_of:
            templete_doc = frappe.get_doc('Item' , variant_of)
            frappe.db.set_value("Item", templete_doc.name, "disabled",1)
            templete_doc.disabled= 0 
            templete_doc.run_method('validate')
            # frappe.throw(str(templete_doc))
            # create_new_item(templete_doc, variant_of=self.variant_of)
    else:
        frappe.throw(f"Failed to Create or Update Item in Magento: {str(response.text)}")
        
        
        
        
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
        if self.image:
            custom_images = ['image' , 'small_image' , 'thumbnail' , 'swatch_image']
            path_image = self.image
            image_name = os.path.basename(path_image)
            custom_attributes.append 
            for image in custom_images:
                custom_attributes.append ({'attribute_code' :image , 'value' : str(image_name)})
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
        name = self.item_code
        visibility = {
            'Not Visible Individually': 1,
            'Catalog': 2,
            'Search': 3,
            'Catalog & Search': 4
        }.get(self.custom_visibility, 1)
        item_group_ids = get_item_groups(self.item_group)
        category_links = [
            {"position": idx, "category_id": id}
            for idx, id in enumerate(item_group_ids)
        ]
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
            vairant_of_sql = frappe.db.sql("SELECT name , custom_item_id FROM tabItem ti WHERE variant_of  =  %s" , self.name  , as_dict = True)
            if len(vairant_of_sql) != 0 :
                for product in vairant_of_sql:
                    if product.custom_item_id !=0:
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