import frappe
from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice , make_delivery_note , update_status
from erpnext.controllers.sales_and_purchase_return import make_return_doc
from erpnext.accounts.doctype.journal_entry.journal_entry import make_reverse_journal_entry
import json


@frappe.whitelist()
def get_payment_channel_amount(child):
    payment_chnnel_amount = 0 
    for row in json.loads(child):
        payment_chnnel_amount += float(row.get('amount') if ( row.get('amount') and row.get('amount') is not None ) else 0 )
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

def get_account(company , customer , with_company= True): 
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
        if account is None and with_company == True : 
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
                title = frappe._("Missing Account"))
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
def deferred_revenue_account(company):
    comp_doc = frappe.get_doc('Company' , company)
    if comp_doc.default_deferred_revenue_account is None:
        frappe.throw('Set Default Deferred Revenue Account in Company {comp}'
                     .format(comp = frappe.utils.get_link_to_form("Company", company) ))
        return None
    return comp_doc.default_deferred_revenue_account 

def create_sales_invoice(self):
        deferred_revenue_acc = deferred_revenue_account(company= self.company)
        if deferred_revenue_acc is None :
                    frappe.throw('Set Default Deferred Revenue Account in Company {comp}'
                     .format(comp = frappe.utils.get_link_to_form("Company", self.company) ))
            
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
            # if doc.items: 
            for item in doc.items: 
                item.enable_deferred_revenue = 1 
                item.deferred_revenue_account = deferred_revenue_acc
                item.service_start_date = self.transaction_date
                item.service_end_date = self.transaction_date
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
                    for item in doc.items: 
                        item.enable_deferred_revenue = 1 
                        item.deferred_revenue_account = deferred_revenue_acc
                        item.service_start_date = self.transaction_date
                        item.service_end_date = self.transaction_date
                    doc.save()
                    doc.submit()
                frappe.msgprint(
                    f'Sales Invoice {existing_invoice["name"]} was cancelled.New Invoice has been Created.', 
                    alert=True, 
                    indicator='orange'
                )


def on_submit(self, method):
    # create_payment_channel_jv(self)
    create_sales_invoice(self)
    create_material_request(self)
    
def on_update_after_submit(self, method):
        if  self.docstatus == 1:
            if self.custom_magento_status == 'On the Way':
                cost_of_delivery_jv(self)
                create_delivery_company_jv(self)
            if self.custom_magento_status == 'Delivered':
                delivery_note = create_delivery_note(self)
                delivery_note_jv(self , delivery_note=delivery_note)
            if self.custom_magento_status == 'Cancelled':
                return_sales_invoice(self)
                # reverse_delivery_note_jv(self)
                return_delivery_note(self)
                reverse_journal_entry(self)
                cancelled_material_request(self)
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
    return target.name

def delivery_note_jv(self , delivery_note):
    delivery_note = frappe.get_doc('Delivery Note' ,delivery_note )
    company_doc = frappe.get_doc("Company", self.company)
    sales_account = company_doc.default_income_account
    revenue_account =deferred_revenue_account(company=self.company)
    cost_center = get_cost_center(self)
    if not sales_account:
                frappe.throw(
                'Set Defualt Income Account Account in Company {company}'
                .format(company = frappe.utils.get_link_to_form("Company", self.company)
                ), 
                titlae = frappe._("Missing Account")
                )
    jv = frappe.new_doc("Journal Entry")
    jv.posting_date = self.transaction_date
    jv.company = self.company
    jv.custom_reference_document = self.doctype
    jv.custom_reference_doctype = self.name
    jv.custom_not_to_reverse = 1 
    dr_row = { 
            'account': revenue_account,
            'debit_in_account_currency' : float(self.custom_total_amount),
            'debit' : float(self.custom_total_amount),
            'cost_center': cost_center,
        }
    jv.append("accounts", dr_row)
    cr_row = { 
                'account' : sales_account, 
                'credit_in_account_currency' :float(self.custom_total_amount),
                'credit' : float(self.custom_total_amount), 
                'cost_center' : cost_center
    }
    jv.append("accounts", cr_row)
    jv.save().submit()

    
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
def reverse_delivery_note_jv(self): 
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
    for dn in list(return_set):
        je = frappe.qb.DocType('Journal Entry')
        linked_jv = (
            frappe.qb.from_(je)
            .select(je.name)
            .where(je.docstatus ==1 )
            .where(je.custom_reference_doctype == dn)
        ).run(as_dict = True)
        if len(linked_jv) != 0 :
            for jv in linked_jv:
                doc = make_reverse_journal_entry(jv.name)
                doc.posting_date = self.transaction_date
                doc.save().submit()
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
    
def reverse_journal_entry(self):
    je = frappe.qb.DocType('Journal Entry')
    linked_jv = (
        frappe.qb.from_(je)
        .select(je.name)
        .where(je.docstatus ==1 )
        .where(je.custom_reference_doctype == self.name)
        .where(je.custom_not_to_reverse == 0 )
    ).run(as_dict = True)
    if len(linked_jv) != 0 :
        for jv in linked_jv:
            doc = make_reverse_journal_entry(jv.name)
            doc.posting_date = self.transaction_date
            doc.save().submit()

@frappe.whitelist()
def delivery_warehouse():
    w = frappe.qb.DocType('Warehouse')
    warehouse = (frappe.qb.from_(w).where(w.warehouse_type == 'Transit').select(w.name)).run(as_dict= True)
    if warehouse and warehouse[0] and  warehouse[0]['name']:
         return  warehouse[0]['name']
    else:
        frappe.throw(
              'Set a lesat One Transit Warehouse.',
              title = frappe._('Missing Transit Warehouse')
         )
        return None
def create_material_request(self):
    tmr = frappe.qb.DocType('Material Request')
    tmri = frappe.qb.DocType('Material Request Item')
    exist_material_request = (
        frappe.qb.from_(tmr)
        .join(tmri).on(tmr.name == tmri.parent).where(tmri.sales_order == self.name)
        .where(tmr.docstatus == 1 ).select(tmr.name)
    ).run()
    if exist_material_request and len(exist_material_request) !=0 :
        frappe.msgprint(
            f'Material Request already created and submitted.', 
            alert=True, 
            indicator='blue'
        )
        return
    target_warehouse = delivery_warehouse()
    mr = frappe.new_doc('Material Request')
    mr.material_request_type = 'Material Transfer'
    schedule_date = self.transaction_date
    mr.transaction_date = self.transaction_date
    mr.schedule_date = schedule_date
    conversion_factor = 1 
    for r in self.items: 
        item = frappe.get_doc('Item' ,r.item_code )
        if len(item.uoms) !=0:
            for uom in item.uoms:
                if uom.uom == r.uom:
                    conversion_factor = uom.conversion_factor
        if len(item.item_defaults) !=0 : 
            item_defaults = (item.item_defaults)[0].as_dict()
            source_warehouse = item_defaults['default_warehouse']
        else:
            stock_setting = frappe.get_doc('Stock Settings')
            source_warehouse = stock_setting.default_warehouse
        data = {
            'item_code' : r.item_code,'item_name': r.item_name,
            'schedule_date':schedule_date,'description': r.description, 
            'qty' : r.qty,'uom': r.uom, 'conversion_factor' : conversion_factor , 
            'stock_qty' : r.qty * conversion_factor,'from_warehouse' : source_warehouse , 
            'warehouse' : target_warehouse,'rate' : r.rate ,'amount' : r.rate * r.qty ,
            'sales_order' : self.name
        }
        mr.append('items' , data)
    mr.save(ignore_permissions = True)
    mr.submit()

def cost_of_delivery_jv(self):
    company_doc = frappe.get_doc('Company' , self.company)
    dc_doc = frappe.get_doc('Customer' , self.custom_delivery_company)
    cost_center = get_cost_center(self)
    cr_account = get_account(company=self.company , customer=self.custom_delivery_company , with_company=False)
    if cr_account is None:
        cr_account = company_doc.default_receivable_account
    if cr_account is None :
        frappe.throw('Delivary Company {dc} Not Have Receivable Account or Define a Defulat Account in Group {dc_group} or in Company {comp}'
                        .format(
                            dc = frappe.utils.get_link_to_form("Customer", self.custom_delivery_company),
                            dc_group =frappe.utils.get_link_to_form("Customer Group", dc_doc.customer_group),
                            comp = frappe.utils.get_link_to_form("Company", self.company) 
                        )
                        , title = frappe._('Missing Account')
                        )
    dr_account = company_doc.custom_cost_of_delivery
    if dr_account is None:
        frappe.throw('Set Default Cost of Delivery Account in Company {comp}'
                     .format(
                        comp = frappe.utils.get_link_to_form("Company", self.company) 
                     )
                     , title = frappe._('Missing Account')
        )
    delivery_cost = dc_doc.custom_delivery_cost
    if delivery_cost in [ None , 0 ]: 
        delivery_company_doc = frappe.get_doc('Customer' , self.custom_delivery_company )
        delivery_cost = delivery_company_doc.custom_delivery_cost
    if delivery_cost in [None , 0]:
        frappe.throw('Set Delivary Cost of Delivery Company {dc}.'
                     .format(dc = frappe.utils.get_link_to_form("Customer", self.custom_delivery_company))
                     , 
                     title = frappe._("Missing Delivery Cost")
        )
    jv = frappe.new_doc("Journal Entry")
    jv.posting_date = self.transaction_date
    jv.company = self.company
    jv.custom_reference_document = self.doctype
    jv.custom_reference_doctype = self.name
    dr_row = { 
            'account': dr_account, 'debit_in_account_currency' : float(delivery_cost),
            'debit' : float(delivery_cost),'party_type': 'Customer',
            'party': self.custom_delivery_company,'cost_center': cost_center,
            'driver' : self.custom_driver
        }
    jv.append("accounts", dr_row)
    cr_row = { 
        'account': cr_account,'credit_in_account_currency' : float(delivery_cost),
        'credit' : float(delivery_cost),'party_type': 'Customer',
        'party': self.custom_delivery_company,'cost_center': cost_center,
        'driver' : self.custom_driver
    }
    jv.append("accounts", cr_row)
    jv.save(ignore_permissions=True)
    jv.submit()

def cancelled_material_request(self): 
    mri = frappe.qb.DocType('Material Request Item')
    pli = frappe.qb.DocType('Pick List Item')
    se = frappe.qb.DocType('Stock Entry')
    material_request = (
        frappe.qb.from_(mri)
        .select(mri.parent)
        .where(mri.sales_order == self.name)
        .groupby(mri.parent)
    ).run(as_dict=True)
    for mr in material_request: 
        pick_list =   (
            frappe.qb.from_(pli)
            .select(pli.parent)
            .where(pli.sales_order == self.name)
            .groupby(pli.parent)
        ).run(as_dict=True)
        if len(pick_list) != 0: 
            for pl in pick_list:
                stock_entry = (
                    frappe.qb.from_(se).select(se.name).where(se.pick_list ==pl.parent )
                ).run(as_dict=True)
                if len(stock_entry) !=0:
                    for loop in stock_entry:
                        se_doc = frappe.get_doc('Stock Entry' , loop.name)
                        se_doc.run_method('cancel')
                pl_doc= frappe.get_doc('Pick List' , pl.parent)
                pl_doc.run_method('cancel')
        mr_doc = frappe.get_doc('Material Request' ,mr.parent )
        mr_doc.run_method('cancel')