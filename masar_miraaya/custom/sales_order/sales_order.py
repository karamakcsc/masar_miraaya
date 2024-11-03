import frappe
from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice , make_delivery_note , update_status
from erpnext.controllers.sales_and_purchase_return import make_return_doc
import json


@frappe.whitelist()
def get_payment_channel_amount(child):
    payment_chnnel_amount = 0 
    for row in json.loads(child):
        payment_chnnel_amount += float(row.get('amount'))
    return payment_chnnel_amount

def validate(self, method):
    validation_payment_channel_amount(self)

def validation_payment_channel_amount(self):
    if self.custom_total_amount is None or self.grand_total is None:
        frappe.throw(
            'Total amount or grand total is missing. Please ensure both values are provided.',
            title=frappe._("Validation Error")
        )
        
    if abs(float(self.custom_total_amount) - float(self.grand_total) ) > 0.001 :
        frappe.throw(
            'The total amount for the item must match the total amount for the payment channels with Cash on Delivery.'
            , title = frappe._("Validation Error")
        )

def cash_on_delivery_account(self):
        company_doc = frappe.get_doc('Company' , self.company)
        if company_doc.custom_default_cash_on_delivery_account in ['' , None]:
            frappe.throw(
                'Set Default Cash on Delivery Account in Company {company}'
                .format(company = frappe.utils.get_link_to_form("Company", self.company)
                ), 
                title = frappe._("Missing Account"))
            return None
        return company_doc.custom_default_cash_on_delivery_account

def get_account(company , customer): 
        account = None
        pc_doc = frappe.get_doc('Customer' , customer) 
        if len(pc_doc.accounts) != 0 :
            for pc_acc in pc_doc.accounts:
                if pc_acc.company == company: 
                    account = pc_acc.account
                    break 
        if account is None : 
            pc_group = frappe.get_doc('Customer Group' , pc_doc.customer_group )
            if len(pc_group.accounts) != 0 :
                for group in pc_group.accounts:
                    if group.company == company : 
                        account = group.account
                        break
        if account is None : 
            company_doc = frappe.get_doc('Company' , company)        
            account = company_doc.custom_receivable_payment_channel if company_doc.custom_receivable_payment_channel else None 
        if account is None:
            frappe.throw('Payment Channel {pc_name} Not HAve Receivable Account or Define a Defulat Account in Group {pc_group} or in Company {comp}'
                        .format(
                            pc_name = frappe.utils.get_link_to_form("Customer", customer),
                            pc_group =frappe.utils.get_link_to_form("Customer Group", pc_doc.customer_group),
                            comp = frappe.utils.get_link_to_form("Company", company) 
                        )
                        , title = frappe._('Missing Account')
                        )
        return account 

def get_cost_center(self):
        if self.cost_center: 
            cost_center = self.cost_center 
        else: 
            company_doc = frappe.get_doc('Company' , self.company)
            cost_center = company_doc.cost_center if company_doc.cost_center else None 
        if cost_center is None : 
            frappe.throw(
                'Set Cost Center or Default Cost Center in Company.',
                title = frappe._("Missing Cost Center"))
        return cost_center
def create_payment_channel_jv(self):
    added_row = None
    cost_center  = get_cost_center(self)
    je  = frappe.qb.DocType('Journal Entry')
    exist_check = (
                    frappe.qb.from_(je)
                    .where(je.custom_reference_doctype == self.name)
                    .select(je.name)
                   ).run(as_dict = True)
    if exist_check and exist_check[0] and exist_check[0]['name']:
        frappe.msgprint(
            f'Journal Entry alerady Created.',
            alert = True , 
            indicator='blue'
        )
        return 
    if self.custom_is_cash_on_delivery and self.custom_cash_on_delivery_amount != 0 : 
        cash_on_delivery_acc = cash_on_delivery_account(self)
        if cash_on_delivery_acc is None:
            frappe.throw(
                'Set Default Cash on Delivery Account in Company {company}'
                .format(company = frappe.utils.get_link_to_form("Company", self.company)
                ), 
                titlae = frappe._("Missing Account"))
        else : 
            added_row =  {
                'account' : cash_on_delivery_acc, 
                'debit_in_account_currency' : self.custom_cash_on_delivery_amount,
                'debit' : self.custom_cash_on_delivery_amount, 
                'cost_center' : cost_center
            }
    jv = frappe.new_doc("Journal Entry")
    jv.posting_date = self.transaction_date
    jv.company = self.company
    jv.custom_reference_document = self.doctype
    jv.custom_reference_doctype = self.name
    for pc in self.custom_payment_channels:
        dr_account = get_account(company= self.company  ,customer= pc.channel)
        dr_row = { 
            'account' : dr_account, 
            'debit_in_account_currency' : pc.amount,
            'debit' : pc.amount, 
            'party_type':'Customer',
            'party': pc.channel,
            'cost_center' : cost_center
        }
        jv.append("accounts", dr_row)
    if added_row is not None : 
        jv.append("accounts", added_row)
    ######### Credit Part 
    cr_account = get_account(company= self.company  ,customer= self.customer)
    cr_row = { 
        'account': cr_account,
        'credit_in_account_currency' : float(self.custom_total_amount),
        'credit' : float(self.custom_total_amount),
        'party_type': 'Customer',
        'party': self.customer,
        'cost_center': cost_center,
    }
    jv.append("accounts", cr_row)
    jv.save(ignore_permissions=True)
    jv.submit()
    frappe.msgprint(
        f"Journal Entry has been Created Successfully." ,
        alert=True , 
        indicator='green'
    )


def create_sales_invoice(self):
        si = frappe.qb.DocType('Sales Invoice')
        sii = frappe.qb.DocType('Sales Invoice Item')
        exist_sales = (
            frappe.qb.from_(si)
            .join(sii).on(si.name == sii.parent)
            .where(sii.sales_order == self.name)
            .select( si.name , si.docstatus)
        ).run(as_dict = True)

        if not exist_sales:
            doc = make_sales_invoice(self.name)
            if doc.items: 
                doc.save()
                doc.submit()
            frappe.msgprint(
                f'Sales Invoice {doc.name} has been created and submitted.', 
                alert=True, 
                indicator='green'
            )
        else:
            existing_invoice = exist_sales[0]
            if existing_invoice['docstatus'] == 1:
                frappe.msgprint(
                    f'Sales Invoice {existing_invoice["name"]} already created and submitted.', 
                    alert=True, 
                    indicator='blue'
                )
            elif existing_invoice['docstatus'] == 2:
                doc = make_sales_invoice(self.name)
                if doc.items:
                    doc.save()
                    doc.submit()
                frappe.msgprint(
                    f'Sales Invoice {existing_invoice["name"]} was cancelled.New Invoice has been Created.', 
                    alert=True, 
                    indicator='orange'
                )




def on_update_after_submit(self, method):
        if  self.docstatus == 1:
            if self.custom_magento_status == 'New':
                create_payment_channel_jv(self)
                create_sales_invoice(self)
            if self.custom_magento_status == 'On the Way':
                create_delivery_company_jv(self)
            if self.custom_magento_status == 'Delivered':
                create_delivery_note(self)
            if self.custom_magento_status == 'Cancelled':
                return_sales_invoice(self)
                return_delivery_note(self)
                cancel_jv(self)
                # update_status(self.name , "Closed")

def create_delivery_company_jv(self):
    if self.custom_is_cash_on_delivery and self.custom_cash_on_delivery_amount != 0 : 

        cost_center = get_cost_center(self)
        jv = frappe.new_doc("Journal Entry")
        jv.posting_date = self.transaction_date
        jv.company = self.company
        jv.custom_reference_document = self.doctype
        jv.custom_reference_doctype = self.name
        cash_on_delivery_acc = cash_on_delivery_account(self)
        if cash_on_delivery_acc is None:
            frappe.throw(
                'Set Default Cash on Delivery Account in Company {company}'
                .format(company = frappe.utils.get_link_to_form("Company", self.company)
                ), 
                title = frappe._("Missing Account"))
        else : 
            cr_row =  {
                'account' : cash_on_delivery_acc, 
                'credit_in_account_currency' : self.custom_cash_on_delivery_amount,
                'credit' : self.custom_cash_on_delivery_amount, 
                'cost_center' : cost_center
            }
            jv.append("accounts", cr_row)

        dr_account = get_account(company= self.company  ,customer= self.custom_delivery_company)
        dr_row = { 
            'account': dr_account,
            'debit_in_account_currency' : float(self.custom_cash_on_delivery_amount),
            'debit' : float(self.custom_cash_on_delivery_amount),
            'party_type': 'Customer',
            'party': self.custom_delivery_company,
            'cost_center': cost_center,
            'driver' : self.custom_driver

        }
        jv.append("accounts", dr_row)
        jv.save(ignore_permissions=True)
        jv.submit()
        frappe.msgprint(
            f"Journal Entry has been Created Successfully." ,
            alert=True , 
            indicator='green'
        )

def create_delivery_note(self):
    target = make_delivery_note(self.name) 
    target.save().submit()

def return_sales_invoice(self):
    sii = frappe.qb.DocType('Sales Invoice Item')
    si = frappe.qb.DocType('Sales Invoice')
    exist_si = (frappe.qb.from_(si)
                .join(sii).on(sii.parent == si.name)
                .select(si.name)
                .where(sii.sales_order == self.name)
                .where(si.docstatus == 1 )
            ).run(as_dict = True)
    lst_si = [si_loop.name for si_loop in exist_si if si_loop.name]
    return_set = set(lst_si)
    for return_si in list(return_set):
        cr_note = make_return_doc("Sales Invoice", return_si, None)
        if cr_note:
            cr_note.save()
            cr_note.submit()

def return_delivery_note(self): 
    dn = frappe.qb.DocType('Delivery Note')
    dni = frappe.qb.DocType('Delivery Note Item')
    exist_dn = (
        frappe.qb.from_(dn)
        .join(dni).on(dn.name == dni.parent)
        .where(dni.against_sales_order == self.name)
        .where(dn.docstatus ==1 )
        .select(dn.name)
        ).run(as_dict = True)
    lst_dn = [dn.name for dn in exist_dn if dn.name]
    return_set = set(lst_dn)
    for return_dn in list(return_set):
            doc = make_return_doc("Delivery Note", return_dn, None)
            if doc : 
                doc.save().submit()
    
def cancel_jv(self):
    je = frappe.qb.DocType('Journal Entry')
    linked_jv = (
        frappe.qb.from_(je)
        .select(je.name)
        .where(je.docstatus ==1 )
        .where(je.custom_reference_doctype == self.name)
    ).run(as_dict = True)
    if len(linked_jv) != 0 :
        for jv in linked_jv:
            jv_doc = frappe.get_doc('Journal Entry' , jv.name)
            jv_doc.run_method('cancel')
