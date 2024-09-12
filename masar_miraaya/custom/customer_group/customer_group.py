import frappe
import requests
from masar_miraaya.api import base_data

def validate(self, method):
    if self.custom_is_publish:
        magento = frappe.get_doc('Magento Sync')
        if magento.sync == 0 :
            create_new_customer_group(self)
        else: 
            frappe.throw("Set Sync in Magento Sync disabled. To Update/Create in magento.")
    
def create_new_customer_group(customer_group_name):
    doc = frappe.get_doc('Customer Group', customer_group_name)
    try:
        base_url, headers = base_data("magento")
        url = base_url + "/rest/V1/customerGroups"
            
        data = {
                "group": {
                    "code": doc.customer_group_name,
                    "tax_class_id": 3,
                }
            }

        if doc.is_new() == 1:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                json_response = response.json()
                customer_group_id = json_response['id']
                doc.custom_customer_group_id = customer_group_id
                frappe.msgprint(f"Customer Group Created Successfully in Magento")
            else:
                frappe.throw(f"Failed To Create Customer Group in Magento: {str(response.text)}")
        else:
            url = base_url + f"/rest/V1/customerGroups/{doc.custom_customer_group_id}"
            
            data = {
                "group": {
                    "code": doc.name,
                    "tax_class_id": 3,
                }
            }
            
            response = requests.put(url, headers=headers, json=data)
            
            if response.status_code == 200:
                frappe.msgprint("Customer Group Updated Successfully in Magento")
            else:
                frappe.throw(f"Failed to Update Customer Group in Magento: {str(response.text)}")

    except Exception as e:
        frappe.throw(f"Failed to create customer group: {str(e)}")