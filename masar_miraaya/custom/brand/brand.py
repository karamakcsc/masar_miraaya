import frappe
def validate(self , method):
        magento = frappe.get_doc('Magento Sync')
        if magento.sync == 0 :
            create_new_brand(self)
        else: 
            frappe.throw("Set Sync in Magento Sync disabled. To Update/Create in magento.")

def before_rename(self , method , old, new, merge ):
    rename_item_group(self , method , old, new, merge)
@frappe.whitelist()    
def create_new_brand(self):
    # try:
        item_group = frappe.db.sql("SELECT name FROM `tabItem Group` WHERE custom_item_group_id = '404'" , as_dict = True)
        if len(item_group) == 0 :
            frappe.throw(f"There is No Item Group Brands Where the Item Group ID Must be 404"
                    )
            return 0 
        exist_item_group_sql = frappe.db.sql("SELECT name , custom_is_publish  FROM `tabItem Group` WHERE name = %s " , (self.name) , as_dict = True)
        print(exist_item_group_sql)
        if len(exist_item_group_sql) == 0 :
            new_item_group = frappe.new_doc("Item Group")
            new_item_group.item_group_name = self.name
            new_item_group.parent_item_group = item_group[0]['name']
            new_item_group.custom_is_publish = self.custom_publish_to_magento
            new_item_group.save(ignore_permissions = True)
        else:
            is_publish = exist_item_group_sql[0]['name']
            if is_publish:
                item_group_doc = frappe.get_doc('Item Group' , exist_item_group_sql[0]['name'])
                item_group_doc.custom_is_publish = self.custom_publish_to_magento
                item_group_doc.save(ignore_permissions = True)
        frappe.msgprint(f"Create Brand in Brands Item Group." , alert=True , indicator=True)       
    # except Exception as e:
    #  #   frappe.throw(f"Failed to create Brand: {str(e)}")

def rename_item_group(self , method , old, new, merge ):
    frappe.rename_doc('Item Group' , old , new)
    