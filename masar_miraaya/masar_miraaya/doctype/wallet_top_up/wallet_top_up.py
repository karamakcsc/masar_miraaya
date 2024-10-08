# Copyright (c) 2024, KCSC and contributors
# For license information, please see license.txt

import frappe
from masar_miraaya.api import base_data
from frappe import _
from frappe.model.document import Document
import requests
import json

class WalletTopup(Document):
    def validate(self):
        self.get_digital_wallet_account()
        self.get_accounts_form_company(with_cost_center=False)
    def on_submit(self):
        #self.adjust_amount_to_wallet_magento()
        self.create_journal_entry()
        
    def get_accounts_form_company(self , with_cost_center):
        account = frappe.db.sql("""
            SELECT 
                custom_gift_card_deferred_account AS gift_account, 
                custom_compensation_expense_account AS comp_account,
                custom_lp_expense_account AS lp_account , 
                cost_center
            FROM `tabCompany`
            WHERE name = %s
        """ , (self.company) , as_dict = True)
        if len(account) !=0 :
            if with_cost_center== False:
                if account[0]['gift_account']:
                    self.gift_card_deferred_account = account[0]['gift_account']
                else:
                    frappe.throw("Set Gift Card Deferred Account in Company." ,title=_("Missing Gift Account") )
                    
                if account[0]['comp_account']:
                    self.compensation_expense_account = account[0]['comp_account']
                else:
                    frappe.throw("Set Compensation Expense Account in Company." ,title=_("Missing Compensation Account") )
                
                if account[0]['lp_account']:
                    self.lp_expense_account = account[0]['lp_account']
                else:
                    frappe.throw("Set LP Expense Account in Company." ,title=_("Missing LP Account") )
            if with_cost_center == True:
                if account[0]['cost_center']:
                    return account[0]['cost_center']
        else:
            frappe.throw("Set Gift Card Deferred, Compensation Expense and LP Expense Accounts in Company." ,title=_("Missing Accounts") )
        
    def get_digital_wallet_account(self):
        account_sql = frappe.db.sql("""
            SELECT 
                tpa.account AS customer_account, 
                tpa2.account AS group_account, 
                tc2.custom_digital_wallet_account AS company_account
            FROM 
                tabCustomer tc 
            INNER JOIN 
                `tabParty Account` tpa ON tpa.parent = tc.name
            LEFT JOIN 
                `tabParty Account` tpa2 ON tpa2.parent = tc.customer_group 
            LEFT JOIN 
                tabCompany tc2 ON tc2.name = %s
            WHERE 
                tc.custom_is_digital_wallet = 1 AND tc.name = %s
        """, (self.company, self.digital_wallet), as_dict=True)

        if  len(account_sql) == 0 :
            frappe.throw("Set Account in one of Customer, Customer Group or Company.", title=_("Missing Account"))

        wallet_account = (account_sql[0]['customer_account'] or 
                          account_sql[0]['group_account'] or 
                          account_sql[0]['company_account'])

        if not wallet_account:
            frappe.throw("Set Account in one of Customer, Customer Group or Company.", title=_("Missing Account"))
        self.wallet_account = wallet_account
        return wallet_account



    def create_journal_entry(self):
        gift_account = self.gift_card_deferred_account
        lp_account = self.lp_expense_account
        comp_account = self.compensation_expense_account
        wallet_account = self.wallet_account
        adj_account = self.wallet_adjustment_account
        cost_center = self.get_accounts_form_company(with_cost_center=True)
        party_type = "Customer"
        party = self.customer
        user_remarks = self.user_remarks
        dimension_account = self.digital_wallet
        
        if self.transaction_type == 'Gift Card':
            debit_account = gift_account
            credit_account = wallet_account
            debit_amount = float(self.topup_amount)
            credit_amount = float(self.topup_amount)
        elif self.transaction_type == 'Loyalty Program (LP)':    
            debit_account = lp_account
            credit_account = wallet_account
            debit_amount = float(self.topup_amount)
            credit_amount = float(self.topup_amount)
        elif self.transaction_type == 'Compensation':
            debit_account = comp_account
            credit_account = wallet_account
            debit_amount = float(self.topup_amount)
            credit_amount = float(self.topup_amount)
        elif self.transaction_type == 'Adjustment':
            debit_amount = abs(float(self.adjustment_amount))
            credit_amount = abs(float(self.adjustment_amount))
            if self.action_type == "Credit":
                debit_account = adj_account
                credit_account = wallet_account
            elif self.action_type ==  "Debit":
                credit_account = adj_account
                debit_account = wallet_account
        jv = frappe.new_doc("Journal Entry")
        jv.posting_date = self.posting_date
        jv.company = self.company
        jv.voucher_type = "Journal Entry"
        jv.custom_reference_document = self.doctype
        jv.custom_reference_doctype = self.name
        debit_accounts = {
                    "account": debit_account,
                    "debit_in_account_currency": debit_amount,
                    "debit" : debit_amount,
                    "cost_center": cost_center,
                    "customer": dimension_account,
                    "user_remark": user_remarks
                    }
        debit_account_doc = frappe.get_doc('Account' ,debit_account )
        if debit_account_doc.account_type in ['Receivable', 'Payable']:
            debit_accounts["party_type"] = party_type
            debit_accounts["party"] = party
        credit_accounts = {
                    "account": credit_account,
                    "credit_in_account_currency": credit_amount,
                    "credit" :credit_amount,
                    "cost_center": cost_center,
                    "customer": dimension_account,
                    "user_remark": user_remarks
                    
                }
        
        creadit_account_doc = frappe.get_doc('Account' ,credit_account )
        if creadit_account_doc.account_type in ['Receivable', 'Payable']:
            credit_accounts["party_type"] = party_type
            credit_accounts["party"] = party
        jv.append("accounts", debit_accounts)
        jv.append("accounts", credit_accounts)
        jv.save(ignore_permissions=True)
        jv.submit()
        frappe.msgprint(f"Journal Entry has been Created Successfully." ,alert=True , indicator='green')
        
        
        
    def adjust_amount_to_wallet_magento(self):
        base_url, headers = base_data("magento")
        url = base_url + "/graphql"
        
        action_type = None
        wallet_amount = 0        
        
        if self.transaction_type != "Adjustment":
            action_type = "credit"
            wallet_amount = self.topup_amount
        elif self.transaction_type == "Adjustment":
            wallet_amount = self.adjustment_amount
            if self.action_type == "Credit":
                action_type = "credit"
            elif self.action_type ==  "Debit":
                action_type = "debit"
        
        payload = {
            "query": f"""
            mutation {{
                adjustamounttowallet(
                    customerIds: "{self.customer_id}"
                    walletamount: {wallet_amount}
                    walletactiontype: "{action_type}"
                    walletnote: "{self.user_remarks}"
                ) {{
                    message
                }}
            }}
            """
        }
        
        response = requests.post(url, headers=headers, json=payload)
        json_response = response.json()
        if response.status_code == 200:
            if 'errors' in json_response:
                frappe.throw(f"Failed to Update Wallet in Magento.")
            else:
                frappe.msgprint(f"Wallet Updated Successfully for Customer: {self.customer} With Amount: {wallet_amount}. in Magento", alert=True, indicator='green')
        else:
            frappe.throw(f"Failed to Update Wallet. {str(response.text)}")