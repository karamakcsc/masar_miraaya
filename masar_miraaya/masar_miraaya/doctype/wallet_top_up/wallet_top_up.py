# Copyright (c) 2024, KCSC and contributors
# For license information, please see license.txt

# import frappe
import frappe
import requests
from datetime import date
from masar_miraaya.api import base_data
from frappe import _
from erpnext.selling.doctype.sales_order.sales_order  import make_sales_invoice 
from frappe.utils import flt, cint

from frappe.model.document import Document


class WalletTopup(Document):
	pass


def on_submit(self, method):
    create_journal_entry(self)
   # pass




@frappe.whitelist()
def create_journal_entry(self):
    account = frappe.db.sql(f""" Select custom_gift_card_expense_account, custom_lp_expense_account, custom_compensation_expense_account, 
                                        custom_adjustment_expense_account, custom_gift_card_deferred_account, custom_lp_deferred_account,
                                        custom_compensation_deferred_account, custom_adjustment_deferred_account
                                    FROM tabComapny    """, as_dict = True )
    debit_gift_account = account[0]['custom_gift_card_deferred_account']
    credit_gift_account = account[0]['custom_gift_card_expense_account']
    debit_lp_account = account[0]['custom_lp_deferred_account']
    credit_lp_account = account[0]['custom_lp_expense_account']
    debit_comp_account = account[0]['custom_compensation_deferred_account']
    credit_comp_account = account[0]['custom_compensation_expense_account']
    debit_adj_account = account[0]['custom_adjustment_deferred_account']
    credit_adj_account = account[0]['custom_adjustment_expense_account']

   

    if self.transaction_type == 'Gift Card':
            if debit_gift_account and credit_gift_account:
                jv = frappe.new_doc("Journal Entry")
                jv.posting_date = self.transaction_date
                jv.company = self.company
                jv.custom_sales_order =  self.name
                debit_accounts = {
                    "account": debit_gift_account,
                    "debit_in_account_currency": float(self.topup_amount),
                    "debit" : float(self.topup_amount),
                    # "cost_center": cost_center,
                    "is_advance": "Yes"
                }
                credit_accounts = {
                    "account": credit_gift_account,
                    "credit_in_account_currency": float(self.topup_amount),
                    "credit" : float(self.topup_amount),
                    # "party_type": "Customer",
                    # "party": self.custom_delivery_company,
                    # "cost_center": cost_center,
                    # "cheque_no": "Sales Order",
                    
                    # "reference_due_date": self.transaction_date,
                    # "user_remark": f"{self.name} - {row.channel_name}"
                }
                jv.append("accounts", debit_accounts)
                jv.append("accounts", credit_accounts)


                
                # frappe.throw(str(debit_accounts))
                jv.save(ignore_permissions=True)
                jv.submit()
                frappe.msgprint(f"Journal Entry has been Created Successfully." ,alert=True , indicator='green')
            else:
                  frappe.throw("Set the E-Comerce Acounts in Company")

    if self.transaction_type == 'Loyalty Program (LP)':
            if debit_lp_account and credit_lp_account:
                jv = frappe.new_doc("Journal Entry")
                jv.posting_date = self.transaction_date
                jv.company = self.company
                jv.custom_sales_order =  self.name
                debit_accounts = {
                    "account": debit_lp_account,
                    "debit_in_account_currency": float(self.topup_amount),
                    "debit" : float(self.topup_amount),
                    # "cost_center": cost_center,
                    "is_advance": "Yes"
                }
                credit_accounts = {
                    "account": credit_lp_account,
                    "credit_in_account_currency": float(self.topup_amount),
                    "credit" : float(self.topup_amount),
                    # "party_type": "Customer",
                    # "party": self.custom_delivery_company,
                    # "cost_center": cost_center,
                    # "cheque_no": "Sales Order",
                    
                    # "reference_due_date": self.transaction_date,
                    # "user_remark": f"{self.name} - {row.channel_name}"
                }
                jv.append("accounts", debit_accounts)
                jv.append("accounts", credit_accounts)


                
                # frappe.throw(str(debit_accounts))
                jv.save(ignore_permissions=True)
                jv.submit()
                frappe.msgprint(f"Journal Entry has been Created Successfully." ,alert=True , indicator='green')

            else:
                  frappe.throw("Set the E-Comerce Acounts in Company")



    if self.transaction_type == 'Compensation':
            if debit_comp_account and credit_comp_account:
                jv = frappe.new_doc("Journal Entry")
                jv.posting_date = self.transaction_date
                jv.company = self.company
                jv.custom_sales_order =  self.name
                debit_accounts = {
                    "account": debit_comp_account,
                    "debit_in_account_currency": float(self.topup_amount),
                    "debit" : float(self.topup_amount),
                    # "cost_center": cost_center,
                    "is_advance": "Yes"
                }
                credit_accounts = {
                    "account": credit_comp_account,
                    "credit_in_account_currency": float(self.topup_amount),
                    "credit" : float(self.topup_amount),
                    # "party_type": "Customer",
                    # "party": self.custom_delivery_company,
                    # "cost_center": cost_center,
                    # "cheque_no": "Sales Order",
                    
                    # "reference_due_date": self.transaction_date,
                    # "user_remark": f"{self.name} - {row.channel_name}"
                }
                jv.append("accounts", debit_accounts)
                jv.append("accounts", credit_accounts)


                
                # frappe.throw(str(debit_accounts))
                jv.save(ignore_permissions=True)
                jv.submit()
                frappe.msgprint(f"Journal Entry has been Created Successfully." ,alert=True , indicator='green')
            else:
                frappe.throw("Set the E-Comerce Acounts in Company")
    if self.transaction_type == 'Adjustment':
            if debit_adj_account and credit_adj_account:
                jv = frappe.new_doc("Journal Entry")
                jv.posting_date = self.transaction_date
                jv.company = self.company
                jv.custom_sales_order =  self.name
                debit_accounts = {
                    "account": debit_adj_account,
                    "debit_in_account_currency": float(self.topup_amount),
                    "debit" : float(self.topup_amount),
                    # "cost_center": cost_center,
                    "is_advance": "Yes"
                }
                credit_accounts = {
                    "account": credit_adj_account,
                    "credit_in_account_currency": float(self.topup_amount),
                    "credit" : float(self.topup_amount),
                    # "party_type": "Customer",
                    # "party": self.custom_delivery_company,
                    # "cost_center": cost_center,
                    # "cheque_no": "Sales Order",
                    
                    # "reference_due_date": self.transaction_date,
                    # "user_remark": f"{self.name} - {row.channel_name}"
                }
                jv.append("accounts", debit_accounts)
                jv.append("accounts", credit_accounts)


                
                # frappe.throw(str(debit_accounts))
                jv.save(ignore_permissions=True)
                jv.submit()
                frappe.msgprint(f"Journal Entry has been Created Successfully." ,alert=True , indicator='green')
            else:
                 frappe.throw("Set the E-Comerce Acounts in Company")



# def cancel_linked_jv(self):
#     linked_jv_sql = frappe.db.sql("SELECT name FROM `tabJournal Entry` WHERE custom_sales_order = %s" , (self.name) , as_dict= True)
#     msg_linked = list()
#     if len(linked_jv_sql) != 0 :
#         for linked_jv in linked_jv_sql:
#             doc = frappe.get_doc('Journal Entry' , linked_jv.name)
#             doc.run_method('cancel')
#             msg_linked.append(linked_jv.name)
#     if len(msg_linked)!=0:
#         msg = 'The Linked Journal Entry are Cancelled:<br><ul>'
#         for jv_linked in msg_linked:
#             msg+=f'<li>Journal Entry : <b>{jv_linked}</b></li>'
#         msg+= '</ul>'
#         frappe.msgprint(msg , title=_("Linked Journal Entry") , indicator='red')
