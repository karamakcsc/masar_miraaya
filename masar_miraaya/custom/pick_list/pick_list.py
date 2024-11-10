import frappe
from erpnext.stock.doctype.pick_list.pick_list import create_stock_entry
import json

@frappe.whitelist()
def packing(self):
    self = frappe._dict(json.loads(self))
    frappe.db.set_value(self.doctype , self.name , 'custom_packed' ,1)
    return 1 
@frappe.whitelist()
def stock_entry_method(self):
    self = frappe._dict(json.loads(self))
    mr_doc = frappe.get_doc('Material Request' , self.material_request)
    assigned_to = assigned_to_me_vaildation(mr_doc)
    if assigned_to: 
        continue_to_role = user_vaildation(assigned_to)
        if continue_to_role:
            allowed_role = role_permission(assigned_to)
            if allowed_role:
                allow_to_cerate_stock_entry  , delivery_company , driver = delivery_company_validation(self)
                if allow_to_cerate_stock_entry:
                    created = stock_entry_creation(self , delivery_company , driver)
                    if created:
                        return True
##

def assigned_to_me_vaildation(self):
    if self.custom_assigned_to is None :
            frappe.throw(
                'The Material Request is not assigned to anyone. You must assign this request to yourself.',
                title=frappe._('Assignment Missing')
            )
            return False
    return self.custom_assigned_to


def user_vaildation(assigned_to):
    if frappe.session.user != assigned_to: 
        frappe.throw(
                'The Material Request is already assigned to {assigned_to}. You cannot assign this request to yourself.'
                .format(assigned_to=assigned_to), 
                title=frappe._('Assigned to Another User')
            )
        return False
    return True 


def role_permission(user):
    role = frappe.get_roles(user)
    if 'Fulfillment User' not in role:
        frappe.throw(
            'You must have the <b>Fulfillment User</b> Role to perform this action.',
            title= frappe._('Role Permission')
        )
        return False
    return True


def delivery_company_validation(self):
    so = None
    for r in self.locations:
        r = frappe._dict(r)
        if hasattr(r ,'sales_order'):
            so = r.sales_order
            break 
    if so: 
        so_doc = frappe.get_doc("Sales Order", so)
        if so_doc.custom_magento_status == 'Cancelled':
            frappe.throw(
                'The Sales Order has been cancelled. You cannot pick the items.'
                , title = frappe._('Cancelled Sales Order')
                )
            return False, None , None 
        if so_doc.custom_delivery_company  is None or so_doc.custom_driver is None : 
            frappe.throw(
                'Delivery Company and Driver are not selected in the Sales Order. The Pick List is not ready for Picking.',
                title=frappe._('Missing Delivery Information')
            )
            return False , None , None 
        return True  , so_doc.custom_delivery_company , so_doc.custom_driver 
    return False , None , None 


def stock_entry_creation(self , delivery_company , driver):
    dict_ = json.dumps(create_stock_entry(json.dumps(self)))
    if bool(dict_) == True and str(dict_) != 'null':
        se_doc = (
            frappe.new_doc('Stock Entry')
            .update(json.loads(dict_))
            .save()
        )
        for row in se_doc.items:
            row.driver = driver
            row.delivery_company = delivery_company
        se_doc.save().submit()
        return True 