import frappe
import requests
import pycountry
from datetime import date
from masar_miraaya.api import base_data
from frappe import _
from erpnext.selling.doctype.sales_order.sales_order  import make_sales_invoice 
from frappe.utils import flt, cint
def on_submit(self, method):
    # create_magento_sales_order(self)
    pass


def validate(self, method):
    calculate_amount(self)
    
def on_change(self, method):
    create_journal_entry(self)
    if self.custom_magento_status == 'Delivered' and self.docstatus == 1:
        create_sales_invoice(self)
    



def create_sales_invoice(self):
    doclist = make_sales_invoice(self.name, ignore_permissions=True)
    doclist.flags.ignore_mandatory = True
    doclist.insert(ignore_permissions = True)
    doclist.submit()
    

@frappe.whitelist()
def create_magento_sales_order(self):
    base_url, headers = base_data("magento")
    
    try:
        customer_doc = frappe.get_doc('Customer', self.customer)
        customer_first_name = customer_doc.custom_first_name
        customer_last_name = customer_doc.custom_last_name
        customer_email = customer_doc.custom_email
        customer_id = customer_doc.custom_customer_id
        customer_store_id = customer_doc.custom_store_id
        customer_website_id = customer_doc.custom_website_id
        customer_doc_name = customer_doc.name
        
        query = frappe.db.sql(""" 
                            SELECT 
                                    ta.address_line1, ta.city, ta.country, ta.pincode,
                                    ta.phone, ta.custom_country_id, ta.email_id, ta.custom_first_name, ta.custom_last_name 
                            FROM tabAddress ta 
                            WHERE custom_customer_id = %s AND is_primary_address = 1 and is_shipping_address = 1
                            """, (customer_id), as_dict=True)
        
        if query and query[0]:
            for data in query:
                address_line = data['address_line1']
                city = data['city']
                country = data['country']
                pincode = data['pincode']
                phone = data['phone']
                country_id = data['custom_country_id']
                email_id = data['email_id']
                first_name = data['custom_first_name']
                last_name = data['custom_last_name']
                
        item_list = []
        if self.get('items'):
            for item in self.get('items'):
                dict_items = {
                    "name": item.item_name,
                    "sku": item.item_code,
                    "qty_ordered": item.qty,
                    "price": item.amount
                }
                item_list.append(dict_items)
        else:
            frappe.throw("Please Add Items")
            
        payload = {
            "entity": {
                "base_currency_code": self.currency,
                "base_grand_total": self.total,
                "created_at": self.transaction_date,
                "customer_email": customer_email,
                "customer_firstname": customer_first_name,
                "customer_lastname": customer_last_name,
                "grand_total": self.grand_total,
                "order_currency_code": self.currency,
                "status": self.custom_sales_order_status.lower(),
                "store_id": customer_store_id,
                "subtotal": self.grand_total,
                "total_qty_ordered": self.total_qty,
                "updated_at": self.delivery_date,
                "items": item_list,
                "billing_address": {
                "firstname": first_name,
                "lastname": last_name,
                "street": [
                    address_line
                ],
                "city": city,
                "postcode": pincode,
                "country_id": country_id,
                "telephone": phone
                },
                "payment": {
                "method": "checkmo"
                },
                "extension_attributes": {
                "shipping_assignments": [
                    {
                    "shipping": {
                        "address": {
                        "firstname": first_name,
                        "lastname": last_name,
                        "street": [
                            address_line
                        ],
                        "city": city,
                        "postcode": pincode,
                        "country_id": country_id,
                        "telephone": phone
                        },
                        "method": "flatrate_flatrate"
                    }
                    }
                ]
                }
            }
            }

        
        url = f"{base_url}/rest/V1/orders" 
        
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code in [200, 201, 202, 203]:
            frappe.msgprint("Sales Order Created Successfully in Magento")
        else:
            frappe.throw(str(f"Error Creating Sales Order in Magento: {response.text}"))
    except Exception as e:
        frappe.throw(str(f"Error Creating Sales Order in Magento: {e}"))

@frappe.whitelist()
def calculate_amount(self):
    total = 0.0
    for row in self.custom_payment_channels:
        total += row.amount
        
    self.custom_total_amount = total


@frappe.whitelist()
def create_journal_entry(self):
    if self.custom_magento_status == 'On the Way' and self.docstatus == 1:

        debit_account_query = frappe.db.sql("SELECT tc.custom_cost_of_delivery , cost_center FROM tabCompany tc WHERE name = %s", (self.company), as_dict = True)
        cost_center = self.cost_center if self.cost_center else debit_account_query[0]['cost_center']
        if cost_center in [ '' , 0 , None]:
            frappe.throw("Set Cost Center in Sales Order or in Company as Defualt Cost Center.")
        if not(debit_account_query and debit_account_query[0] and debit_account_query[0]['custom_cost_of_delivery']):
            frappe.throw(f"Set Debit Account in Company in Default Cost of Delivery." , title=_("Missing Debit Account"))
            return
        debit_account = debit_account_query[0]['custom_cost_of_delivery']
        account = frappe.db.sql("""SELECT tpa.account AS `customer_account`, tpa2.account AS `customer_group_account`, tc2.custom_receivable_payment_channel AS `company_account` 
                                    FROM tabCustomer tc 
                                    INNER JOIN `tabParty Account` tpa ON tpa.parent = tc.name 
                                    LEFT JOIN `tabCustomer Group` tcg ON tcg.name = tc.customer_group 
                                    LEFT JOIN `tabParty Account` tpa2 ON tpa2.parent = tcg.name 
                                    LEFT JOIN tabCompany tc2 ON tpa2.company = tc2.name
                                    WHERE tc.name = %s AND tc.custom_is_delivery = 1""", (self.custom_delivery_company), as_dict = True)
        if len(account) != 0:
            if account and account[0]:
                if account[0]['customer_account']:
                    credit_account = account[0]['customer_account']
                elif account[0]['customer_group_account']:
                    credit_account = account[0]['customer_group_account']
                elif account[0]['company_account']:
                    credit_account = account[0]['company_account']
        else:
            frappe.throw(f"Set Default Account in Customer: {self.custom_delivery_company}, or Company: {self.company}")  
            
        if credit_account in ['', None]:
            frappe.throw(f"Set Default Account in Customer: {self.custom_delivery_company}, or Company: {self.company}")
        jv = frappe.new_doc("Journal Entry")
        jv.posting_date = self.transaction_date
        jv.company = self.company
        debit_accounts = {
            "account": debit_account,
            "debit_in_account_currency": float(self.grand_total),
            "debit" : float(self.grand_total),
            "cost_center": cost_center,
            "is_advance": "Yes"
        }
        credit_accounts = {
            "account": credit_account,
            "credit_in_account_currency": float(self.grand_total),
            "credit" : float(self.grand_total),
            "party_type": "Customer",
            "party": self.custom_delivery_company,
            "cost_center": cost_center,
            # "reference_type": "Sales Order",
            # "reference_name": self.name,
            # "reference_due_date": self.transaction_date,
            # "user_remark": f"{self.name} - {row.channel_name}"
        }
        jv.append("accounts", debit_accounts)
        jv.append("accounts", credit_accounts)


        
        # frappe.throw(str(jv.as_dict()))
        jv.save(ignore_permissions=True)
        jv.submit()
