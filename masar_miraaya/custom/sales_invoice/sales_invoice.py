import frappe
import json
from erpnext.accounts.general_ledger import make_gl_entries


def on_submit(self, method):
    #pass
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
        customer_account = frappe.db.sql("""
            SELECT tpa.account AS `customer_account`
            FROM `tabCustomer` tc 
            INNER JOIN `tabParty Account` tpa ON tc.name = tpa.parent 
            WHERE tc.custom_is_digital_wallet = 1 AND tc.name = %s
        """, (row.channel), as_dict=True)

        customer_group_account = None
        if not customer_account:
            customer_group_account = frappe.db.sql("""
                SELECT tpa.account AS `customer_group_account`
                FROM `tabCustomer` tc 
                INNER JOIN `tabCustomer Group` tcg ON tc.customer_group = tcg.name 
                INNER JOIN `tabParty Account` tpa ON tcg.name = tpa.parent 
                WHERE tc.name = %s
            """, (row.channel), as_dict=True)

        company_account = None
        if not customer_group_account:
            company_account = frappe.db.sql("""
                SELECT custom_receivable_payment_channel AS `company_account`
                FROM `tabCompany`
                WHERE name = %s
            """, (self.company,), as_dict=True)
        debit_account = (customer_account[0]['customer_account'] if customer_account 
                        else customer_group_account[0]['customer_group_account'] if customer_group_account 
                        else company_account[0]['company_account'] if company_account
                        else None)

        if not debit_account:
            frappe.throw(f"Set Default Account in Customer: {row.channel_name}, or Company: {self.company}")

        gl_entries.append(
            self.get_gl_dict({
                "account": debit_account,
                "against": company_account[0]['company_account'] if company_account else None,
                "debit_in_account_currency": row.amount,
                "debit": row.amount,
                "party_type": "Customer",
                "party": row.channel,
                "remarks": row.channel + ' : ' + self.name,
                "voucher_type": self.doctype,
                "voucher_no": self.name
            })
        )
    company_account_entry = company_account[0]['company_account'] if company_account else None
    gl_entries.append(
        self.get_gl_dict({
            "account": company_account_entry,
            "against": debit_account,
            "credit_in_account_currency": self.grand_total,
            "credit": self.grand_total,
            "cost_center": cost_center,
            "party_type": "Customer",
            "party": self.customer,
            "remarks": self.name,
            "voucher_type": self.doctype,
            "voucher_no": self.name
        })
    )

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

def delete_linked_gl_entries(self):
    cancelled_doc = frappe.db.sql_list("""select name from tabEmployee Resignation 
    where docstatus = 2 """)
    frappe.db.sql("""delete from tabGL Entry 
                where voucher_type = 'Employee Resignation' and voucher_no in (%s)""" 
                % (', '.join(['%s']*len(cancelled_doc))), tuple(cancelled_doc))