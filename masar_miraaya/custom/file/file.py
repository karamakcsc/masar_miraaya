import frappe
from masar_miraaya.custom.item.item import add_image_to_item, get_magento_image_id
def validate(self, method):
    if self.attached_to_doctype == 'Item' and self.custom_magento_sync == 0 :
        doc = frappe.get_doc('Item', self.attached_to_name)
        file_path = self.file_url
        add_image_to_item(doc, file_path)

def on_trash(self, method):
    if self.attached_to_doctype == 'Item':
        doc = frappe.get_doc('Item', self.attached_to_name)
        get_magento_image_id(doc, self.file_name)
