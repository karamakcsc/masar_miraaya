import frappe
from erpnext.stock.doctype.pick_list.pick_list import  PickList
import json
from masar_miraaya.api import change_magento_status_to_fullfilled

def on_submit(self , method):
    assigned_to_validate(self)
    user_vaildation(self)
    
    
def assigned_to_validate(self): 
    if self.custom_assigned_to is None: 
        frappe.throw(
            '''Please ensure that you click the "Assign To Me" button before submitting. 
            This step is necessary to assign this pick to yourself.''', 
            title = frappe._('Assign Validation')
        )
def user_vaildation(self):
    if frappe.session.user != self.custom_assigned_to: 
        frappe.throw(
                'Pick List is already assigned to {assigned_to}. You cannot assign this request to yourself.'
                .format(assigned_to=self.custom_assigned_to), 
                title=frappe._('Assigned to Another User')
            )
        return False
    return True 
@frappe.whitelist()
def packing(self):
    self = frappe._dict(json.loads(self))
    linked_so = get_linked_so(self)
    error , continue_ = change_magento_status(linked_so)
    if continue_:
        change_so_status(linked_so)
        PickList.create_stock_reservation_entries(self= frappe.get_doc(self.doctype , self.name) , notify=True)
        frappe.db.set_value(self.doctype , self.name , 'custom_packed' ,1)
        return 1 
    else : 
        frappe.throw('Error Magento Connection : {error}'.format(error = error))

def change_magento_status(linked_so): 
    text = 'Magento ID is None or Sales Order is Not Submitted.' 
    for so in linked_so:
        so_doc = frappe.get_doc('Sales Order' , so.so_name)
        if so_doc.docstatus == 1 and so_doc.custom_magento_id is not None:  
            text , status_code = change_magento_status_to_fullfilled(so_doc.custom_magento_id)
            if status_code  in [200 , 201]:
                return  text , True
    return text , False

def change_so_status(linked_so):
    if len(linked_so) != 0 : 
        for so in linked_so:
            so_doc = frappe.get_doc('Sales Order' , so.so_name)
            if so_doc.docstatus == 1:
                so_doc.custom_magento_status = 'Fullfilled'
                so_doc.save() 

def get_linked_so(self):
    pl = frappe.qb.DocType(self.doctype)
    pli = frappe.qb.DocType('Pick List Item')
    linked_so = (
        frappe.qb.from_(pl)
        .join(pli).on(pl.name == pli.parent)
        .select((pli.sales_order).as_('so_name'))
        .where(pl.name == self.name)
        .groupby(pli.sales_order)
    ).run(as_dict = True)
    return linked_so
                
@frappe.whitelist()
def assign_to_me(self):
    self = frappe._dict(json.loads(self))
    user = frappe.session.user
    role = frappe.get_roles(user)
    if 'Fulfillment User' not in role:
            frappe.throw(
                'User {user} does not have the "Fulfillment User" role assigned and therefore cannot be assigned the Material Request.'
                .format(user = user),
                title = frappe._('Role Validation')
                )
            return None
    if self.custom_assigned_to is not None : 
            frappe.throw(
                'The Material Request is already assigned to {assigned_to}. You cannot assign this request to yourself.'
                .format(assigned_to=self.custom_assigned_to), 
                title=frappe._('Assigned to Another User')
            )
            return None 
    frappe.db.set_value(self.doctype, self.name, "custom_assigned_to", user)
    frappe.db.commit()
    return user