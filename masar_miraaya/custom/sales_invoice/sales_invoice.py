import frappe
import json
from erpnext.accounts.general_ledger import make_gl_entries
from masar_miraaya.custom.sales_order.sales_order import get_account , cash_on_delivery_account

def on_submit(self, method):
    make_gl(self)
    
    
def make_gl(self):
    gl_entries = []
    for item in self.items:
        if item.sales_order:
            sales_order = frappe.get_doc("Sales Order", item.sales_order)
    if sales_order: 
        company_doc = frappe.get_doc("Company", self.company)
        main_customer_account = get_account(company=self.company , customer=self.customer , with_company=False)
        if main_customer_account is None: 
            main_customer_account = company_doc.default_receivable_account
        company_cost_center = company_doc.cost_center
        cost_center = self.cost_center if self.cost_center else company_cost_center
        if cost_center in [ '' , 0 , None]:
            frappe.throw("Set Cost Center in Sales Order or in Company as Defualt Cost Center.")
            
        account = None 
        for r in sales_order.custom_payment_channels:
            account = get_account(company=self.company , customer=r.channel)

            if self.is_return == 0 :
                gl_entries.append(
                    self.get_gl_dict({
                        "account": account,
                        "against": main_customer_account ,
                        "cost_center": cost_center,
                        "debit_in_account_currency": abs(r.amount),
                        "debit": abs(r.amount),
                        "party_type": "Customer",
                        "party": r.channel,
                        "remarks": r.channel + ' : ' + self.name,
                        "voucher_type" : self.doctype , 
                        "voucher_no" : self.name
                    }))
            elif self.is_return == 1 : 
                gl_entries.append(
                    self.get_gl_dict({
                        "account": account,
                        "against": main_customer_account ,
                        "cost_center": cost_center,
                        "credit_in_account_currency":abs( r.amount),
                        "credit": abs(r.amount),
                        "party_type": "Customer",
                        "party": r.channel,
                        "remarks": r.channel + ' : ' + self.name,
                        "voucher_type" : self.doctype , 
                        "voucher_no" : self.name
                    }))
        ################## Cash on Delivery
        if self.is_return == 0 : 
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
                    "voucher_type" : self.doctype , 
                    "voucher_no" : self.name
                }))
        elif self.is_return == 1 : 
            gl_entries.append(
                self.get_gl_dict({
                    "account": main_customer_account,
                    "against": account,
                    "debit_in_account_currency":abs(sales_order.custom_payment_channel_amount),
                    "debit": abs(sales_order.custom_payment_channel_amount),
                    "cost_center": cost_center,
                    "party_type": "Customer",
                    "party": self.customer,
                    "remarks": self.name,
                    "voucher_type" : self.doctype , 
                    "voucher_no" : self.name
                }))
        if sales_order.custom_is_cash_on_delivery and sales_order.custom_cash_on_delivery_amount != 0 :
            cash_on_delivery_acc = cash_on_delivery_account(self)
            if cash_on_delivery_acc is None:
                frappe.throw(
                    'Set Default Cash on Delivery Account in Company {company}'
                    .format(company = frappe.utils.get_link_to_form("Company", self.company)
                    ), 
                    title = frappe._("Missing Account"))
            if self.is_return == 0 : 
                gl_entries.append(
                    self.get_gl_dict({
                        "account": cash_on_delivery_acc,
                        "against": main_customer_account,
                        "cost_center": cost_center,
                        "debit_in_account_currency": abs(sales_order.custom_cash_on_delivery_amount),
                        "debit":abs(sales_order.custom_cash_on_delivery_amount),
                        "voucher_type" : self.doctype , 
                        "voucher_no" : self.name
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
                    "voucher_type" : self.doctype , 
                    "voucher_no" : self.name
                }))
            elif self.is_return == 1 : 
                gl_entries.append(
                    self.get_gl_dict({
                        "account": cash_on_delivery_acc,
                        "against": main_customer_account,
                        "cost_center": cost_center,
                        "credit_in_account_currency": abs(sales_order.custom_cash_on_delivery_amount),
                        "credit":abs(sales_order.custom_cash_on_delivery_amount),
                        "voucher_type" : self.doctype , 
                        "voucher_no" : self.name
                    }))
                
                gl_entries.append(
                    self.get_gl_dict({
                        "account": main_customer_account,
                        "against": cash_on_delivery_acc,
                        "debit_in_account_currency":abs(sales_order.custom_cash_on_delivery_amount),
                        "debit": abs(sales_order.custom_cash_on_delivery_amount),
                        "cost_center": cost_center,
                        "party_type": "Customer",
                        "party": self.customer,
                        "remarks": self.name,
                        "voucher_type" : self.doctype , 
                        "voucher_no" : self.name
                    }))
        ###########   
        if gl_entries:
            make_gl_entries(gl_entries, cancel=0, adv_adj=0)
