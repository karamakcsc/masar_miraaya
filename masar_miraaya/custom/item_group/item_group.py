import frappe
import requests
from masar_miraaya.api import base_data , request_with_history

def validate(self, method):
    # frappe.throw("HHH")
    roles = (frappe.get_roles(frappe.session.user))
    if (self.custom_is_publish and ('API Integration' not in roles)) or (self.custom_is_publish and frappe.session.user == 'Administrator' ):
        magento = frappe.get_doc('Magento Sync')
        if magento.sync == 0 :  
            item_group_in_magento(self)
        else: 
            frappe.throw("Set Sync in Magento Sync disabled. To Update/Create in magento.")
       
            
def before_rename(self, method, old, new, merge):
   if self.custom_is_publish:
        magento = frappe.get_doc('Magento Sync')
        if magento.sync == 0 :  
            remane_in_magento(self, method, old, new, merge)
        else: 
            frappe.throw("Set Sync in Magento Sync disabled. To Update/Create in magento.")
@frappe.whitelist()
def check_brands(name , parent_item_group_id):
    
    old_perant = (frappe.db.sql("SELECT custom_parent_item_group_id FROM `tabItem Group` WHERE name = %s" , (name) , as_dict=True))
    if old_perant and old_perant[0] and old_perant[0]['custom_parent_item_group_id'] and int(old_perant[0]['custom_parent_item_group_id']) == 404 :
        return (f'To Create/Update Item Group in Brands Parent. you Must Create it From Brand.')
    if parent_item_group_id and int(parent_item_group_id) == 404 :
        return (f'To Create/Update Item Group in Brands Parent. you Must Create it From Brand.')
        
def item_group_in_magento(self):
    if self.custom_item_group_id in [None , 0 , '']:
        new_item_group_in_magento(self)
    else:
        update_item_group_in_magento(self)
        

def new_item_group_in_magento(self):
    base_url, headers = base_data("magento")
    url = base_url + f"/rest/V1/categories/0"
    if not self.custom_parent_item_group_id:
        frappe.throw("Set Perant Item Group")
    disabled = self.custom_disabled
    data = {
            "category": {
                "parent_id": self.custom_parent_item_group_id,
                "name": self.name,
                "is_active":not  bool(disabled),
                "position": 1,
                "include_in_menu": True
            }
        }
    print(data)
    response = request_with_history(
                    req_method='PUT', 
                    document=self.doctype, 
                    doctype=self.name, 
                    url=url, 
                    headers=headers  ,
                    payload=data        
                )
    if response.status_code == 200:
            json_response = response.json()
            group_id = json_response['id']
            magento_name = json_response['name']
            print(json_response)
            self.custom_item_group_id = group_id
            self.name = f"{group_id} - {self.item_group_name}"
            # frappe.rename_doc("Item Group", self.name, new_item_group_name)
            frappe.msgprint("Category Created Successfully in Magento", alert = True, indicator = 'green')

def update_item_group_in_magento(self):
        base_url, headers = base_data("magento")
        url = base_url + f"/rest/V1/categories/{self.custom_item_group_id}"
        check_response = request_with_history(
                    req_method='GET', 
                    document=self.doctype, 
                    doctype=self.name, 
                    url=url, 
                    headers=headers
                )
        if check_response.status_code == 200:
            json_response = check_response.json()
        else:
            frappe.throw(f"Error While Sync with Mogento: {str(json_response)}")
        update_in_magento = False
        if json_response['name'] != self.name.split(' - ', 1)[-1].strip():
            new_name =  self.name.split(' - ', 1)[-1].strip()
            update_in_magento = True
        else:
           new_name =  self.name.split(' - ', 1)[-1].strip() 
        if bool(json_response['is_active']) != (not  bool(  self.custom_disabled)) :
            new_is_active = not  bool( self.custom_disabled)
            update_in_magento = True
        else:
            new_is_active = not  bool(  self.custom_disabled)
        if json_response['parent_id'] != self.custom_parent_item_group_id:
                url_to_update = base_url + f"/rest/V1/categories/{self.custom_item_group_id}/move"
                data = {
                    "parentId": self.custom_parent_item_group_id,
                }
                response = request_with_history(
                    req_method='PUT', 
                    document=self.doctype, 
                    doctype=self.name, 
                    url=url_to_update, 
                    headers=headers  ,
                    payload=data        
                )
                if response.status_code == 200:
                    frappe.msgprint('Perant Item Group Updated Successflly.' , alert=True , indicator='green')
        if update_in_magento:
            url = base_url + f"/rest/all/V1/categories/{self.custom_item_group_id}"
            data ={ 
                   "category": {
                    "parent_id": self.custom_parent_item_group_id,
                    "name":new_name,
                    "is_active": new_is_active, ###############################################33
                    "position": 1,
                    "include_in_menu": True
                }
            }
            response_update = request_with_history(
                    req_method='PUT', 
                    document=self.doctype, 
                    doctype=self.name, 
                    url=url, 
                    headers=headers  ,
                    payload=data        
                )
            if response_update.status_code == 200:
                    json_response = response_update.json()
                    group_id = json_response['id']
                    print(json_response)
                    if self.custom_item_group_id != group_id:
                        frappe.throw("Cant Complete Sync with Magento")
        frappe.msgprint('Magento was updated successfully.' , alert=True , indicator='green')
def remane_in_magento(self, method, old, new, merge):
        base_url, headers = base_data("magento")
        url = base_url + f"/rest/all/V1/categories/{self.custom_item_group_id}"
        check_response = request_with_history(
                    req_method='GET', 
                    document=self.doctype, 
                    doctype=self.name, 
                    url=url, 
                    headers=headers
                )
        if check_response.status_code == 200:
            json_response = check_response.json()
        else:
            frappe.throw(f"Error While Sync with Mogento (Remane): {str(json_response)}")
        new_name = new.split(' - ', 1)[-1].strip()
        magento_name = json_response['name']
        if new_name != magento_name:
            data ={ 
                   "category": {
                    "parent_id": self.custom_parent_item_group_id,
                    "name":new_name,
                    "is_active": bool( not self.custom_disabled),
                    "position": 1,
                    "include_in_menu": True
                }
            } 
            response_update = request_with_history(
                    req_method='PUT', 
                    document=self.doctype, 
                    doctype=self.name, 
                    url=url, 
                    headers=headers  ,
                    payload=data        
                )
            if response_update.status_code == 200:
                    json_response = response_update.json()
                    group_id = json_response['id']
                    if self.custom_item_group_id != group_id:
                        frappe.throw("Cant Complete Sync with Magento")
                    frappe.msgprint('The rename operation in Magento was updated successfully.' , alert=True , indicator='green')