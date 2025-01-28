# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class VariantConverter(Document):
    def validate(self):
        self.validate_items()
        
    def on_submit(self):
        self.update_item_to_variant()
    
    
    def validate_items(self):
        for item in self.items:
            existing_doc = frappe.db.sql("""
                SELECT tvci.item_code
                FROM `tabVariant Converter` tvc
                INNER JOIN `tabVariant Converter Item` tvci ON tvci.parent = tvc.name 
                WHERE tvc.docstatus = 1 AND tvci.item_code = %s
            """, (item.item_code,), as_dict=True)
            
            if existing_doc and existing_doc[0] and existing_doc[0]['item_code']:
                frappe.throw(
                    f"Item {item.item_code} is already in another doc."
                )
            
    
    def update_item_to_variant(self):
        template = frappe.get_doc("Item", self.template_item)
        for item in self.items:
            frappe.db.set_value("Item", item.item_code, "variant_of", self.template_item)
            frappe.db.set_value("Item", item.item_code, "variant_based_on", "Item Attribute")
            item_doc = frappe.get_doc("Item", item.item_code)
            for d in template.attributes:
                attribute_value = None
                item_doc.attributes = []
                if d.attribute.lower() == "color":
                    attribute_value = item.color
                elif d.attribute.lower() == "shade":
                    attribute_value = item.shade
                elif d.attribute.lower() == "size":
                    attribute_value = item.size
                elif d.attribute.lower() == "size (ml)":
                    attribute_value = item.size_ml
                if attribute_value:
                    frappe.get_doc({
                        "doctype": "Item Variant Attribute",
                        "parent": item.item_code,
                        "parentfield": "attributes",
                        "parenttype": "Item",
                        "variant_of": self.template_item,
                        "attribute": d.attribute,
                        "attribute_value": attribute_value
                    }).insert()
            # item_doc.run_method("save")
            # check_value = item_doc.grant_commission
            # new_check = not check_value
            # item_doc.grant_commission = new_check
            # item_doc.grant_commission = check_value
            # item_doc.save()
            # frappe.throw(str(new_check))


    @frappe.whitelist()
    def set_temp_attributes(self):
        template_attributes = frappe.db.sql("""
            SELECT DISTINCT tiva.attribute
            FROM `tabItem Variant Attribute` tiva
            WHERE tiva.parent = %s
        """, (self.template_item,), as_dict=True)
        
        return [attr['attribute'] for attr in template_attributes]
    
    @frappe.whitelist()
    def get_attributes(self):
        color , shade , size , size_ml = [''] , [''] ,[''] , ['']
        attributes = frappe.db.sql("""
            SELECT tia.attribute_name, tiav.attribute_value 
            FROM `tabItem Attribute` tia 
            INNER JOIN `tabItem Attribute Value` tiav ON tiav.parent = tia.name
            WHERE tia.attribute_name IN ("Color", "shade", "Size", "Size (ml)")
        """, as_dict=True)
        for a in attributes: 
            if a.attribute_name == 'Color': 
                color.append(a.attribute_value )
            elif a.attribute_name == 'shade': 
                shade.append(a.attribute_value )
            elif a.attribute_name == 'Size': 
                size.append(a.attribute_value )
            elif a.attribute_name == 'Size (ml)': 
                size_ml.append(a.attribute_value )
        return {
            'color':color, 
            'size':size, 
            'shade':shade, 
            'size_ml':size_ml
                }