import frappe
import json



@frappe.whitelist()
def role_validate(self):
    self = frappe._dict(json.loads(self))
    user = frappe.session.user
    role = frappe.get_roles(user)
    if 'Carrier' in role:
        if self.get('custom_assigned_to') != user and self.get('custom_assigned_to') is not None :
            frappe.throw("You are not assigned to this doc.")
            return 0 
    assign_validate(self)

@frappe.whitelist()            
def assign_validate(self):
    # frappe.throw(str(self))
    # self = frappe._dict(json.loads(self))
    
    user = frappe.session.user
    so_name = None
    for row in self.get('items'):
        so_name = row.get('sales_order')
        break
    if so_name:
        so_doc = frappe.get_doc("Sales Order", so_name)
        if not so_doc.custom_delivery_company and not so_doc.custom_driver or so_doc.custom_magento_status == 'Cancelled':
            frappe.throw("This Order is Not Ready to be Picked")
            return
        else:
            frappe.db.set_value("Material Request", self.name, "custom_assigned_to", user)
            frappe.db.commit()