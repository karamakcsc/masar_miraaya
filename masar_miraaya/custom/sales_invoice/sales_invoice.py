import frappe
import json
from erpnext.accounts.general_ledger import make_gl_entries


def on_submit(self, method):
    
    make_gl(self)
    
    
def make_gl(self):
    gl_entries = []
    for item in self.items:
        if item.sales_order:
            sales_order = frappe.get_doc("Sales Order", item.sales_order)
        else:
            frappe.throw(f"Set Sales Order Reference in Row: {item.idx}")
        
    company_doc = frappe.get_doc("Company", self.company)
    company_account = company_doc.default_receivable_account
    company_cost_center = company_doc.cost_center
    cost_center = self.cost_center if self.cost_center else company_cost_center
    if cost_center in [ '' , 0 , None]:
        frappe.throw("Set Cost Center in Sales Order or in Company as Defualt Cost Center.")
    if not company_account:
        frappe.throw("Set Default Income Account in Company")
    
    for row in sales_order.custom_payment_channels:
        account = frappe.db.sql("""
                        SELECT 
                        tpa.account AS `customer_account`, 
                        tpa2.account AS `customer_group_account`
                        FROM tabCustomer tc 
                        LEFT JOIN `tabParty Account` tpa  ON tpa.parent =tc.name
                        LEFT JOIN `tabParty Account` tpa2 ON tpa2.parent = tc.customer_group
                        WHERE tc.name = %s AND tc.custom_is_payment_channel = 1
            """, (row.channel), as_dict = True)
        if len(account) != 0:
            if account and account[0] and (account[0]['customer_account'] or account[0]['customer_group_account']):
                debit_account = (account[0]['customer_account'] or 
                            account[0]['customer_group_account'])
            else:
                debit_account_sql = frappe.db.sql("""SELECT custom_receivable_payment_channel  AS company_account FROM tabCompany WHERE name = %s
                                """, (self.company) , as_dict = True )  
                if len(debit_account_sql) != 0 :
                        debit_account = debit_account_sql[0]['company_account']
            
        if debit_account in ['', None]:
            frappe.throw(f"Set Default Account in Customer: {row.channel_name}, or Company: {self.company}")
        
        gl_entries.append(
            self.get_gl_dict({
                "account": debit_account,
                "against": company_account ,
                "debit_in_account_currency": row.amount,
                "debit": row.amount,
                "party_type": "Customer",
                "party": row.channel,
                "remarks": row.channel + ' : ' + self.name,
                "voucher_type" : self.doctype , 
                "voucher_no" : self.name
            }))
     
     ################## Cash on Delivery 
    account_delivery_sql = frappe.db.sql("""
                        SELECT 
                        tpa.account AS `customer_account`, 
                        tpa2.account AS `customer_group_account` 
                        FROM tabCustomer tc 
                        LEFT JOIN `tabParty Account` tpa  ON tpa.parent =tc.name
                        LEFT JOIN `tabParty Account` tpa2 ON tpa2.parent = tc.customer_group
                        WHERE tc.name = %s
            """, ( sales_order.custom_delivery_company), as_dict = True)
    
    if len(account_delivery_sql) != 0:
        if account_delivery_sql and account_delivery_sql[0] and (account_delivery_sql[0]['customer_account'] or account_delivery_sql[0]['customer_group_account']):
            account_delivery = (account_delivery_sql[0]['customer_account'] or 
                          account_delivery_sql[0]['customer_group_account'] )
        else:
            delivery_sql = frappe.db.sql("""SELECT custom_receivable_payment_channel  AS company_account FROM tabCompany WHERE name = %s
                                """, (self.company) , as_dict = True )  
            if len(delivery_sql) != 0 :
                        account_delivery = delivery_sql[0]['company_account']
    if account_delivery in ['', None]:
            frappe.throw(f"Set Default Account in Customer: {sales_order.custom_delivery_company}, or Company: {self.company}")
    gl_entries.append(
            self.get_gl_dict({
                "account": account_delivery,
                "against": company_account,
                "debit_in_account_currency": sales_order.custom_cash_on_delivery_amount,
                "debit":sales_order.custom_cash_on_delivery_amount,
                "party_type": "Customer",
                "party": sales_order.custom_delivery_company , 
                "remarks": sales_order.custom_delivery_company + ' : ' + self.name,
                "voucher_type" : self.doctype , 
                "voucher_no" : self.name
            })) 
    ###########      
    gl_entries.append(
    self.get_gl_dict({
        "account": company_account,
        "against": debit_account,
        "credit_in_account_currency": self.grand_total,
        "credit": self.grand_total,
        "cost_center": cost_center,
        "party_type": "Customer",
        "party": self.customer,
        "remarks": self.name,
        "voucher_type" : self.doctype , 
        "voucher_no" : self.name
    }))
    if gl_entries:
        make_gl_entries(gl_entries, cancel=0, adv_adj=0)

def cancel_linked_gl_entries(self):
    gl_entries = frappe.get_all("GL Entry",filters={"voucher_type": self.doctype, "voucher_no": self.name, "docstatus": 1},pluck="parent",distinct=True,)
    for gl_entry in gl_entries:
        gl_entry_doc = frappe.get_doc("GL Entry", gl_entry.name)
        gl_entry_doc.docstatus = 2
        gl_entry_doc.save()
        self.db_set("gl_entries_created", 0)
        self.db_set("gl_entries_submitted", 0)
        self.set_status(update=True, status="Cancelled")
        self.db_set("error_message", "")