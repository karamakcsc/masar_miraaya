import frappe
from erpnext.stock.doctype.pick_list.pick_list import  PickList
import json
from masar_miraaya.api import change_magento_status_to_fullfilled
from frappe.query_builder.functions import  Sum
def on_submit(self , method):
    items_validation(self)
    qty_validation(self)
    assigned_to_validate(self)
    user_vaildation(self)
    
def items_validation(self):
    linked_so = get_linked_so(self)
    soi = frappe.qb.DocType('Sales Order Item')
    i =  frappe.qb.DocType('Item')
    for so in linked_so:
        if so.so_name:
            sql = (
                    frappe.qb.from_(soi)
                    .join(i)
                    .on(soi.item_code == i.name)
                    .select(
                        (i.name).as_('item_code'),
                            (soi.name).as_('row_id'), (soi.idx))
                    .where(soi.parent == so.so_name)
                    .where(i.is_stock_item ==1 )
                    ).run(as_dict = True)
            item_lst = [loop.item_code for loop in sql]
            row_lst = [loop.row_id for loop in sql]
            for location in self.locations:
                if location.item_code not in item_lst: # or location.sales_order_item not in row_lst:
                    frappe.throw(
                        'The item {item} is currently part of a sales order and must be picked along with other items.'
                        .format(item = location.item_code), 
                        title=frappe._('Item Pickup Notice')
                    )
            items_lst = list()
            for l in self.locations: 
                items_lst.append(l.sales_order_item)
            for r in sql:
                if r.row_id not in items_lst:
                    frappe.throw(
                        'Item {item} at index {idx} in the Sales Order is missing or not found.'
                        .format(item = r.item_code , idx=r.idx),
                        title=frappe._('Sales Order Item Missing')
                    )
            
            
            
def qty_validation(self): 
    linked_so = get_linked_so(self)
    soi = frappe.qb.DocType('Sales Order Item')
    i =  frappe.qb.DocType('Item')
    pli = frappe.qb.DocType('Pick List Item')
    for so in linked_so:
        if so.so_name:
            items = (
                    frappe.qb.from_(soi)
                    .join(i).on(soi.item_code == i.name)
                    .select(
                        (i.name) , 
                        Sum(soi.qty).as_('qty') , 
                    )
                    .where(soi.parent == so.so_name)
                    .where(i.is_stock_item ==1 )
                    .groupby(soi.item_code)
                    ).run(as_dict = True)
            for item in items: 
                qty = (frappe.qb.from_(pli)
                    .select(Sum(pli.qty).as_('qty')
                            , Sum(soi.picked_qty).as_('picked_qty'))
                    .where(pli.parent == self.name)
                    .where(pli.item_code == item.name)
                    .groupby(pli.item_code)
                ).run(as_dict = True)[0]
                if qty['qty'] != item.qty or qty['picked_qty'] != item.qty:
                    
                    frappe.throw(
                        '''The quantity for item {item} does not match the sales order quantity, 
                        or the picked quantity does not match the sales order quantity. 
                        Both quantities must be equal.'''
                        .format(item = item.name),
                    title=frappe._('Quantity Mismatch Error')
                    )      
        
def assigned_to_validate(self): 
    if self.custom_assigned_to is None: 
        frappe.throw(
            '''Please ensure that you click the "Assign To Me" button before submitting. 
            This step is necessary to assign this pick to yourself.''', 
            title = frappe._('Assign Validation')
        )
@frappe.whitelist()
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
    self = frappe._dict(json.loads(self))##
    linked_so = get_linked_so(self)##
    error , continue_ = change_magento_status(linked_so)############# Magento
    if continue_: ############# Magento
        change_so_status(linked_so)
        PickList.create_stock_reservation_entries(self= frappe.get_doc(self.doctype , self.name) , notify=True)
        frappe.db.set_value(self.doctype , self.name , 'custom_packed' ,1)
        return 1 
    else : ############# Magento
        frappe.throw('Error Magento Connection : {error}'.format(error = str(error))) ############# Magento

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
                so_doc.save(ignore_permissions=True)

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
    if 'Picker' not in role:
            frappe.throw(
                'User {user} does not have the "Picker" role assigned and therefore cannot be assigned the Stock Entry.'
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
    frappe.db.set_value(self.doctype, self.name, "custom_assigned", 1)
    frappe.db.commit()
    return user


@frappe.whitelist()
def user_validation_picker(self):
   
    self = frappe.get_doc(json.loads(self))
    if not self.custom_assigned_to:
        frappe.throw(
            'The Pick list is not assigned. Please assign it to yourself.',
            title=frappe._('Assigned to Yourself')
        )
        return False
    if frappe.session.user != self.custom_assigned_to:
        frappe.throw(
            'Pick List is already assigned to {assigned_to}. You cannot assign this request to yourself.'.format(
                assigned_to=self.custom_assigned_to
            ),
            title=frappe._('Assigned to Another User')
        )
        return False
    return True
