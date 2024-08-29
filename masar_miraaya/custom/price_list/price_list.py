import frappe
from frappe import _


def validate(self , method ):
    if self.custom_magento_selling:
        exist_magento_selling = frappe.db.sql(
            "SELECT name FROM `tabPrice List` WHERE custom_magento_selling = 1 AND enabled = 1 AND name != %s",
            (self.name,), 
            as_dict=1
        )
        if exist_magento_selling:
            frappe.throw(
                f"Magento Selling already exists in another Price List: {exist_magento_selling[0]['name']} (Only one Price List allowed)",
                title=_("Existing Magento Selling")
            )
        
        if self.selling == 0:
            frappe.throw(
                "Magento Selling must be enabled with the Selling check",
                title=_("Magento Selling Requirement")
            )

