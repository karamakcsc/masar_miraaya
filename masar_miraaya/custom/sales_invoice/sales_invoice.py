import frappe
import json
from erpnext.accounts.general_ledger import make_gl_entries
from masar_miraaya.custom.sales_order.sales_order import get_account, cash_on_delivery_account

def on_submit(self, method):
    make_gl(self)

def validate(self , method): 
    if self.is_return == 1:
        set_return_account(self)  

def make_gl(self):
    if self.is_return == 0:
        make_gl_normal(self)
    elif self.is_return == 1: 
        set_return_account(self)
        make_gl_return(self)

def make_gl_normal(self):
    gl_entries = []
    for item in self.items:
        if item.sales_order:
            sales_order = frappe.get_doc("Sales Order", item.sales_order)
    if sales_order: 
        company_doc = frappe.get_doc("Company", self.company)
        main_customer_account = get_account(company=self.company, customer=self.customer)
        if main_customer_account is None: 
            main_customer_account = company_doc.default_receivable_account
        company_cost_center = company_doc.cost_center
        cost_center = self.cost_center if self.cost_center else company_cost_center
        if cost_center in ['', 0, None]:
            frappe.throw("Set Cost Center in Sales Order or in Company as Default Cost Center.")
        
        account = None 
        for r in sales_order.custom_payment_channels:
            account = get_account(company=self.company, customer=r.channel)
            if r.amount not in [None, 0]:
                gl_entries.append(
                    self.get_gl_dict({
                        "account": account,
                        "against": main_customer_account,
                        "cost_center": cost_center,
                        "debit_in_account_currency": abs(r.amount),
                        "debit": abs(r.amount),
                        "party_type": "Customer",
                        "party": r.channel,
                        "customer": self.customer,
                        "remarks": r.channel + ' : ' + self.name,
                        "voucher_type": self.doctype, 
                        "voucher_no": self.name
                    }))
        
        if sales_order.custom_payment_channel_amount not in [None, 0]:
            gl_entries.append(
                self.get_gl_dict({
                    "account": main_customer_account,
                    "against": account,
                    "credit_in_account_currency": abs(sales_order.custom_payment_channel_amount),
                    "credit": abs(sales_order.custom_payment_channel_amount),
                    "cost_center": cost_center,
                    "party_type": "Customer",
                    "party": self.customer,
                    "remarks": self.name,
                    "voucher_type": self.doctype, 
                    "voucher_no": self.name
                }))
        
        if sales_order.custom_is_cash_on_delivery and sales_order.custom_cash_on_delivery_amount != 0:
            cash_on_delivery_acc = cash_on_delivery_account(self)
            if cash_on_delivery_acc is None:
                frappe.throw(
                    'Set Default Cash on Delivery Account in Company {company}'
                    .format(company=frappe.utils.get_link_to_form("Company", self.company)), 
                    title=frappe._("Missing Account"))
            
            if sales_order.custom_cash_on_delivery_amount not in [None, 0]:
                gl_entries.append(
                    self.get_gl_dict({
                        "account": cash_on_delivery_acc,
                        "against": main_customer_account,
                        "cost_center": cost_center,
                        "debit_in_account_currency": abs(sales_order.custom_cash_on_delivery_amount),
                        "debit": abs(sales_order.custom_cash_on_delivery_amount),
                        "voucher_type": self.doctype, 
                        "voucher_no": self.name
                    }))
                
                gl_entries.append(
                    self.get_gl_dict({
                        "account": main_customer_account,
                        "against": cash_on_delivery_acc,
                        "credit_in_account_currency": abs(sales_order.custom_cash_on_delivery_amount),
                        "credit": abs(sales_order.custom_cash_on_delivery_amount),
                        "cost_center": cost_center,
                        "remarks": self.name,
                        "party_type": "Customer",
                        "party": self.customer,
                        "voucher_type": self.doctype, 
                        "voucher_no": self.name
                    }))
        
        if gl_entries:
            credits, debits = 0, 0
            for g in gl_entries:
                credits += g.get('credit', 0)
                debits += g.get('debit', 0)
            if credits != debits:
                frappe.throw(f"Total credits {credits} and debits {debits} do not match.{str(gl_entries)}")
            make_gl_entries(gl_entries, cancel=0, adv_adj=0)

def make_gl_return(self): 
    for item in self.items:
        if item.sales_order:
            sales_order = frappe.get_doc("Sales Order", item.sales_order)
    
    delivery_note = [dn.parent for dn in frappe.get_all(
        "Delivery Note Item",
        filters={"against_sales_order": sales_order.name},
        fields=["parent"],
        distinct=True
    )]
    
    if len(delivery_note) != 0: 
        make_gl_delivered(self)
    else: 
        make_unearned_reclassification_gl(self)

def get_digital_wallet():
    return frappe.db.sql("SELECT name FROM `tabCustomer` WHERE custom_is_digital_wallet = 1")[0][0]

def make_gl_delivered(self):
    gl_entries = []
    wallet_name = get_digital_wallet()
    main_customer_account = get_account(company=self.company, customer=self.customer)
    wallet_acc = get_account(company=self.company, customer=wallet_name)
    
    gl_entries.append(
        self.get_gl_dict({
            "account": main_customer_account,
            "against": wallet_acc,
            "cost_center": self.cost_center,
            "debit_in_account_currency": abs(self.grand_total),
            "debit": abs(self.grand_total),
            "party_type": "Customer",
            "party": self.customer,
            "remarks": self.name,
            "voucher_type": self.doctype, 
            "voucher_no": self.name
        }))
    
    gl_entries.append(
        self.get_gl_dict({
            "account": wallet_acc,
            "against": main_customer_account,
            "cost_center": self.cost_center,
            "credit_in_account_currency": abs(self.grand_total),
            "credit": abs(self.grand_total),
            "party_type": "Customer",
            "party": wallet_name,
            "customer": self.customer,
            "remarks": wallet_name + ' : ' + self.name,
            "voucher_type": self.doctype, 
            "voucher_no": self.name
        }))        
    
    if gl_entries:
        credits, debits = 0, 0
        for g in gl_entries:
            credits += g.get('credit', 0)
            debits += g.get('debit', 0)
        if credits != debits:
            frappe.throw(f"Total credits {credits} and debits {debits} do not match.{str(gl_entries)}")
        make_gl_entries(gl_entries, cancel=0, adv_adj=0)        

def make_unearned_reclassification_gl(self):
    gl_entries = []
    for item in self.items:
        if item.sales_order:
            sales_order = frappe.get_doc("Sales Order", item.sales_order)
    
    if sales_order: 
        company_doc = frappe.get_doc("Company", self.company)
        main_customer_account = get_account(company=self.company, customer=self.customer)
        if main_customer_account is None: 
            main_customer_account = company_doc.default_receivable_account
        company_cost_center = company_doc.cost_center
        cost_center = self.cost_center if self.cost_center else company_cost_center
        if cost_center in ['', 0, None]:
            frappe.throw("Set Cost Center in Sales Order or in Company as Default Cost Center.")
        
        account = None 
        for r in sales_order.custom_payment_channels:
            account = get_account(company=self.company, customer=r.channel)
            if r.amount not in [None, 0]:
                gl_entries.append(
                    self.get_gl_dict({
                        "account": account,
                        "against": main_customer_account,
                        "cost_center": cost_center,
                        "credit_in_account_currency": abs(r.amount),
                        "credit": abs(r.amount),
                        "party_type": "Customer",
                        "party": r.channel,
                        "customer": self.customer,
                        "remarks": r.channel + ' : ' + self.name,
                        "voucher_type": self.doctype, 
                        "voucher_no": self.name
                    }))
        
        if sales_order.custom_payment_channel_amount not in [None, 0]:
            gl_entries.append(
                self.get_gl_dict({
                    "account": main_customer_account,
                    "against": account,
                    "debit_in_account_currency": abs(sales_order.custom_payment_channel_amount),
                    "debit": abs(sales_order.custom_payment_channel_amount),
                    "cost_center": cost_center,
                    "party_type": "Customer",
                    "party": self.customer,
                    "remarks": self.name,
                    "voucher_type": self.doctype, 
                    "voucher_no": self.name
                }))
        
        if sales_order.custom_is_cash_on_delivery and sales_order.custom_cash_on_delivery_amount != 0:
            cash_on_delivery_acc = cash_on_delivery_account(self)
            if cash_on_delivery_acc is None:
                frappe.throw(
                    'Set Default Cash on Delivery Account in Company {company}'
                    .format(company=frappe.utils.get_link_to_form("Company", self.company)), 
                    title=frappe._("Missing Account"))
            
            if sales_order.custom_cash_on_delivery_amount not in [None, 0]:
                gl_entries.append(
                    self.get_gl_dict({
                        "account": cash_on_delivery_acc,
                        "against": main_customer_account,
                        "cost_center": cost_center,
                        "credit_in_account_currency": abs(sales_order.custom_cash_on_delivery_amount),
                        "credit": abs(sales_order.custom_cash_on_delivery_amount),
                        "voucher_type": self.doctype, 
                        "voucher_no": self.name
                    })) 
                
                gl_entries.append(
                    self.get_gl_dict({
                        "account": main_customer_account,
                        "against": cash_on_delivery_acc,
                        "debit_in_account_currency": abs(sales_order.custom_cash_on_delivery_amount),
                        "debit": abs(sales_order.custom_cash_on_delivery_amount),
                        "cost_center": cost_center,
                        "remarks": self.name,
                        "party_type": "Customer",
                        "party": self.customer,
                        "voucher_type": self.doctype, 
                        "voucher_no": self.name
                    }))
        
        if gl_entries:
            credits, debits = 0, 0
            for g in gl_entries:
                credits += g.get('credit', 0)
                debits += g.get('debit', 0)
            if credits != debits:
                frappe.throw(f"Total credits {credits} and debits {debits} do not match.{str(gl_entries)}")
            make_gl_entries(gl_entries, cancel=0, adv_adj=0)

def set_return_account(self): 
    return_acc = frappe.get_value('Company', self.company, 'custom_default_return_income_account')
    revenue_acc = frappe.get_value('Company', self.company, 'default_deferred_revenue_account')
    if return_acc is None:
        frappe.throw(
            'Set Default Return Income Account in Company {company}'
            .format(company=frappe.utils.get_link_to_form("Company", self.company)), 
            title=frappe._("Missing Account"))
    if revenue_acc is None:
        frappe.throw(
            'Set Default Deferred Revenue Account in Company {company}'
            .format(company=frappe.utils.get_link_to_form("Company", self.company)), 
            title=frappe._("Missing Account"))
    
    for item in self.items:
        if item.sales_order:
            sales_order = frappe.get_doc("Sales Order", item.sales_order)
    
    delivery_note = [dn.parent for dn in frappe.get_all(
        "Delivery Note Item",
        filters={"against_sales_order": sales_order.name},
        fields=["parent"],
        distinct=True
    )]
    
    if len(delivery_note) != 0: 
        for i in self.items:
            if self.docstatus == 1:
                frappe.db.set_value('Sales Invoice Item', i.name, 'income_account', return_acc)
            else:
                i.income_account = return_acc
    else:
        for i in self.items:
            if self.docstatus == 1:
                frappe.db.set_value('Sales Invoice Item', i.name, 'income_account', revenue_acc)
            else:
                i.income_account = revenue_acc