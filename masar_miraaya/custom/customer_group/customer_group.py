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

def after_rename(self, method, old, new, merge):
    if self.custom_is_publish:
        magento = frappe.get_doc('Magento Sync')
        if magento.sync == 0 :
            update_customer_group(self)
        else: 
            frappe.throw("Set Sync in Magento Sync disabled. To Update/Create in magento.")


def create_new_customer_group(self):
    try:
        if self.custom_customer_group_id in ['', 0, None, ' ']:
            base_url, headers = base_data("magento")
            get_url = base_url + "/rest/default/V1/customerGroups/search?searchCriteria="
            get_response = requests.get(get_url, headers=headers)
            if get_response.status_code == 200:
                json_response = get_response.json()
                for group in json_response['items']:
                    if group['code'] == self.customer_group_name:
                        frappe.throw("The Customer Group Already Exists In Magento")
                
                url = base_url + "/rest/V1/customerGroups"
                            
                data = {
                        "group": {
                            "code": self.customer_group_name,
                            "tax_class_id": 3
                        }
                    }

                response = requests.post(url, headers=headers, json=data)
                if response.status_code == 200:
                    json_response = response.json()
                    customer_group_id = json_response['id']
                    self.custom_customer_group_id = customer_group_id
                    frappe.msgprint(f"Customer Group Created Successfully in Magento" , alert=True , indicator='green')
                else:
                    frappe.throw(f"Failed To Create Customer Group in Magento: {str(response.text)}")
    except Exception as e:
        frappe.throw(f"Failed to create customer group: {str(e)}")
        
def update_customer_group(self):
    try:
        base_url, headers = base_data("magento")
        get_url = base_url + "/rest/default/V1/customerGroups/search?searchCriteria="
        get_response = requests.get(get_url, headers=headers)
        if get_response.status_code == 200:
            json_response = get_response.json()
            for group in json_response['items']:
                if group['id'] == self.custom_customer_group_id and group['code'] != self.name:
                    base_url, headers = base_data("magento")
                    url = base_url + f"/rest/V1/customerGroups/{self.custom_customer_group_id}"
                    data = {
                        "group": {
                        "code": self.name,
                        "tax_class_id": 3,
                        }
                    }
                    response = requests.put(url, headers=headers, json=data)
                    if response.status_code == 200:
                        json_response = response.json()
                        customer_group_id = json_response['id']
                        self.custom_customer_group_id = customer_group_id
                        frappe.msgprint(f"Customer Group Updated Successfully in Magento" , alert=True , indicator='green')
                    else:
                        frappe.throw(f"Failed To Updated Customer Group in Magento: {str(response.text)}")
    except Exception as e:
        frappe.throw(f"Failed to rename customer group: {str(e)}")