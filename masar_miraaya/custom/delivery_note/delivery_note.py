
import frappe
from masar_miraaya.custom.sales_order.sales_order import get_account
from erpnext.accounts.general_ledger import make_gl_entries
def on_submit(self, method) : 
    make_gl(self)




def make_gl(self):
    gl_entries = []
    for item in self.items:
        if item.against_sales_order:
            sales_order = frappe.get_doc("Sales Order", item.against_sales_order)
        
    if sales_order: 
        company_doc = frappe.get_doc("Company", self.company)
        sales_account = company_doc.default_receivable_account
        company_cost_center = company_doc.cost_center
        cost_center = self.cost_center if self.cost_center else company_cost_center
        if cost_center in [ '' , 0 , None]:
            frappe.throw("Set Cost Center in Sales Order or in Company as Defualt Cost Center.")
        if not sales_account:
                frappe.throw(
                'Set Defualt Income Account Account in Company {company}'
                .format(company = frappe.utils.get_link_to_form("Company", self.company)
                ), 
                titlae = frappe._("Missing Account")
                )
        for row in sales_order.custom_payment_channels: 
                dr_account = get_account(company=sales_order.company , customer=row.channel)
                if self.is_return == 0: 
                    gl_entries.append(
                        self.get_gl_dict({
                            "account": dr_account,
                            "against": sales_account ,
                            "debit_in_account_currency": abs(row.amount),
                            "debit": abs(row.amount),
                            "party_type": "Customer",
                            "party": row.channel,
                            "remarks": row.channel + ' : ' + self.name,
                            "voucher_type" : self.doctype , 
                            "voucher_no" : self.name
                        }))
                elif self.is_return == 1: 
                    gl_entries.append(
                        self.get_gl_dict({
                            "account": dr_account,
                            "against": sales_account ,
                            "credit_in_account_currency": abs(row.amount),
                            "credit": abs(row.amount),
                            "party_type": "Customer",
                            "party": row.channel,
                            "remarks": row.channel + ' : ' + self.name,
                            "voucher_type" : self.doctype , 
                            "voucher_no" : self.name
                        }))
        if self.is_return == 0 : 
            gl_entries.append(
             self.get_gl_dict({
                            "account": sales_account,
                            "against":  dr_account,
                            "credit_in_account_currency": abs(sales_order.custom_payment_channel_amount),
                            "credit": abs(sales_order.custom_payment_channel_amount),
                            "party_type": "Customer",
                            "party": row.channel,
                            "remarks": row.channel + ' : ' + self.name,
                            "voucher_type" : self.doctype , 
                            "voucher_no" : self.name
            }))
        elif self.is_return == 1 : 
            gl_entries.append(
             self.get_gl_dict({
                            "account": sales_account,
                            "against":  dr_account,
                            "debit_in_account_currency": abs(sales_order.custom_payment_channel_amount),
                            "debit": abs(sales_order.custom_payment_channel_amount),
                            "party_type": "Customer",
                            "party": row.channel,
                            "remarks": row.channel + ' : ' + self.name,
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