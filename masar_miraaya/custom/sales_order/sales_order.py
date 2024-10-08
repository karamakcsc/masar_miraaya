import frappe
import requests
from datetime import date
from masar_miraaya.api import base_data
from frappe import _
from erpnext.selling.doctype.sales_order.sales_order  import make_sales_invoice 
from frappe.utils import flt, cint
import json

def on_submit(self, method):
    # create_magento_sales_order(self)
    pass


def validate(self, method):
    # calculate_amount(self)
    validation_payment_channel(self)
    
def on_update_after_submit(self, method):
    if self.custom_magento_status == 'On the Way' and self.docstatus == 1:
        create_journal_entry(self)
        create_stock_entry(self)
    if self.custom_magento_status == 'Delivered' and self.docstatus == 1:
        create_sales_invoice(self)
    # if self.custom_magento_status == 'Delivered' and self.docstatus == 1:
    #     create_sales_invoice(self)
    
def on_cancel(self , method):
    cancel_linked_jv(self)
    
    

def validation_payment_channel(self):
    if self.custom_total_amount is None or self.grand_total is None:
        frappe.throw(
            'Total amount or grand total is missing. Please ensure both values are provided.',
            title=_("Validation Error")
        )
        
    if abs(float(self.custom_total_amount) - float(self.grand_total) ) > 0.001 :
        frappe.throw(
            'The total amount for the item must match the total amount for the payment channels with Cash on Delivery.'
            , title = _("Validation Error")
        )
        
@frappe.whitelist()
def create_magento_sales_order(self):
    base_url, headers = base_data("magento")
    
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
                "price": item.rate,
                "discount": item.discount_amount
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
    if response.status_code == 200:
        frappe.msgprint("Sales Order Created Successfully in Magento", alert=True , indicator='green')
    else:
        frappe.throw(str(f"Error Creating Sales Order in Magento: {str(response.text)}"))

@frappe.whitelist()
def get_payment_channel_amount(child):
    payment_chnnel_amount = 0 
    for row in json.loads(child):
        payment_chnnel_amount += float(row.get('amount'))
    return payment_chnnel_amount
    
# @frappe.whitelist()
# def calculate_amount(self):
#     total = 0.0
#     for row in self.custom_payment_channels:
#         total += row.amount
        
#     self.custom_total_amount = total


@frappe.whitelist()
def create_journal_entry(self):
        linked_jv_sql = frappe.db.sql("SELECT name FROM `tabJournal Entry` WHERE custom_reference_doctype = %s" , (self.name) , as_dict= True)
        if (linked_jv_sql and linked_jv_sql[0] and linked_jv_sql[0]['name']):
            frappe.msgprint(f"Journal Entry alerady Created for this Sales Order" ,alert=True , indicator='blue')
            return
        else:
            debit_account_query = frappe.db.sql("""SELECT tc.custom_cost_of_delivery , 
                                        custom_receivable_payment_channel  AS company_account,
                                        cost_center FROM tabCompany tc WHERE name = %s""", (self.company), as_dict = True)
            cost_center = self.cost_center if self.cost_center else debit_account_query[0]['cost_center']
            if cost_center in [ '' , 0 , None]:
                frappe.throw("Set Cost Center in Sales Order or in Company as Defualt Cost Center.")
            if not(debit_account_query and debit_account_query[0] and debit_account_query[0]['custom_cost_of_delivery']):
                frappe.throw(f"Set Debit Account in Company in Default Cost of Delivery." , title=_("Missing Debit Account"))
                return
            debit_account = debit_account_query[0]['custom_cost_of_delivery']
            if not self.custom_delivery_company:
                frappe.throw(f"Set Delivery Company." , title=_("Missing Delivery Company"))
                return
            account = frappe.db.sql("""SELECT 
                                    tpa.account AS `customer_account`, 
                                    tpa2.account AS `customer_group_account`
                                FROM tabCustomer tc 
                                INNER JOIN 
                                    `tabParty Account` tpa ON tpa.parent = tc.name 
                                LEFT JOIN 
                                    `tabCustomer Group` tcg ON tcg.name = tc.customer_group 
                                LEFT JOIN 
                                    `tabParty Account` tpa2 ON tpa2.parent = tcg.name 
                                WHERE 
                                    tc.name = %s AND tc.custom_is_delivery = 1""", (self.custom_delivery_company), as_dict = True)
            
            credit_account = None
            if account:
                credit_account = account[0]['customer_account'] 
                if credit_account is None:
                    credit_account = account[0]['customer_group_account']
            if  credit_account is None:
                    credit_account = debit_account_query[0]['company_account']
                        
            if credit_account in ['', None]:
                frappe.throw(f"Set Default Account in Customer: {self.custom_delivery_company}, or Company: {self.company}")
                
            delivery_fees_doc = frappe.get_doc('Customer' ,self.custom_delivery_company)
            delivery_fees = delivery_fees_doc.custom_delivery_fees
            if delivery_fees in[0 , None]:
                frappe.throw(f"Set Delivery Fees in Customer:{self.custom_delivery_company}")
            jv = frappe.new_doc("Journal Entry")
            jv.posting_date = self.transaction_date
            jv.company = self.company
            jv.custom_reference_document = self.doctype
            jv.custom_reference_doctype = self.name
            debit_accounts = {
                "account": debit_account,
                "debit_in_account_currency": float(delivery_fees),
                "debit" : float(delivery_fees),
                "cost_center": cost_center,
                "is_advance": "Yes"
            }
            credit_accounts = {
                "account": credit_account,
                "credit_in_account_currency": float(delivery_fees),
                "credit" : float(delivery_fees),
                "party_type": "Customer",
                "party": self.custom_delivery_company,
                "cost_center": cost_center,
            }
            jv.append("accounts", debit_accounts)
            jv.append("accounts", credit_accounts)
            jv.save(ignore_permissions=True)
            jv.submit()
            frappe.msgprint(f"Journal Entry has been Created Successfully." ,alert=True , indicator='green')
            
def create_sales_invoice(self):
        exist_sales = frappe.db.sql("""
            SELECT 
                tsi.name, tsi.docstatus FROM `tabSales Invoice` tsi
            INNER JOIN `tabSales Invoice Item` tsii 
            ON tsi.name = tsii.parent 
            WHERE tsii.sales_order = %s
        """, (self.name), as_dict=True)

        if not exist_sales:
            from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice
            doc = make_sales_invoice(self.name)
            doc.update_stock = 1
            if doc.items: 
                for item in doc.items:
                    item.to_driver = self.custom_driver
                    # item.to_delivery_company = self.custom_delivery_company 
                doc.save()
                doc.submit()
            frappe.msgprint(f'Sales Invoice {doc.name} has been created and submitted.', alert=True, indicator='green')
        
        else:
            existing_invoice = exist_sales[0]
            
            if existing_invoice['docstatus'] == 1:
                frappe.msgprint(f'Sales Invoice {existing_invoice["name"]} already created and submitted.', alert=True, indicator='blue')
            
            elif existing_invoice['docstatus'] == 2:
                from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice
                doc = make_sales_invoice(self.name)
                doc.update_stock = 1
                if doc.items: 
                    for item in doc.items:
                        item.to_driver = self.custom_driver
                        # item.to_delivery_company = self.custom_delivery_company 
                    doc.save()
                    doc.submit()
                frappe.msgprint(f'Sales Invoice {existing_invoice["name"]} was canceled.New Invoice has been Created.', alert=True, indicator='orange')
       

def cancel_linked_jv(self):
    linked_jv_sql = frappe.db.sql("SELECT name FROM `tabJournal Entry` WHERE custom_reference_doctype = %s" , (self.name) , as_dict= True)
    msg_linked = list()
    if len(linked_jv_sql) != 0 :
        for linked_jv in linked_jv_sql:
            doc = frappe.get_doc('Journal Entry' , linked_jv.name)
            doc.run_method('cancel')
            msg_linked.append(linked_jv.name)
    if len(msg_linked)!=0:
        msg = 'The Linked Journal Entry are Cancelled:<br><ul>'
        for jv_linked in msg_linked:
            msg+=f'<li>Journal Entry : <b>{jv_linked}</b></li>'
        msg+= '</ul>'
        frappe.msgprint(msg , title=_("Linked Journal Entry") , indicator='red')


def create_stock_entry(self):
    se_type = 'Material Transfer'
    se_target = 'Delivery - KCSC'
    stock_setting = frappe.get_doc('Stock Settings')
    setting_source = stock_setting.default_warehouse
    se = frappe.new_doc('Stock Entry')
    se.stock_entry_type = se_type
    for item in self.items:
        data = {
            's_warehouse' : item.warehouse if item.warehouse else setting_source , 
            't_warehouse' : se_target , 
            'item_code'  : item.item_code , 
            'item_name' : item.item_name , 
            'qty' : item.qty , 
            'uom':item.uom ,
            'to_driver' :self.custom_driver
            # 'to_delivery_company' : self.custom_delivery_company 
        }
        se.append('items' , data)
    se.save(ignore_permissions = True)
    se.submit()



