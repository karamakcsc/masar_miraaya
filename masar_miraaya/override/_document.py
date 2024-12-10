import frappe 
def validate_amended_from_override(self):
    if self.doctype != 'Sales Order':
        if frappe.db.get_value(self.doctype, self.get("amended_from"), "docstatus") != 2:
            message = (
				"{0} cannot be amended because it is not cancelled. Please cancel the document before creating an amendment."
			).format(frappe.utils.get_link_to_form(self.doctype, self.get("amended_from")))
            frappe.throw(message, title=("Amendment Not Allowed"))