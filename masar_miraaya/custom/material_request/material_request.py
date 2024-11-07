import frappe
import json
@frappe.whitelist()
def assign_me(self):
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
    frappe.db.set_value("Material Request", self.name, "custom_assigned_to", user)
    frappe.db.commit()
    return user