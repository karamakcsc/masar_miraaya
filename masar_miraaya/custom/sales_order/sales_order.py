import frappe
from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice , make_delivery_note , update_status , create_pick_list
from erpnext.controllers.sales_and_purchase_return import make_return_doc
from erpnext.accounts.doctype.journal_entry.journal_entry import make_reverse_journal_entry
import json
from erpnext.stock.doctype.pick_list.pick_list import ( 
                validate_item_locations,     stock_entry_exists ,   update_stock_entry_based_on_work_order,
                update_stock_entry_based_on_material_request ,update_stock_entry_items_with_no_reference )
from masar_miraaya.api import change_magento_status_to_cancelled
from datetime import datetime
from masar_miraaya.api import base_data
import requests
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
    create_sales_invoice(self)
    create_draft_pick_list(self)
    
def on_update_after_submit(self, method):
        if  self.docstatus == 1:
            if self.custom_magento_status == 'On the Way':
                cost_of_delivery_jv(self)
                create_delivery_company_jv(self)
                stock_entry_method(self)
            if self.custom_magento_status == 'Delivered':
                cancel_stock_reservation_entry(self)
                delivery_note = create_delivery_note(self)
                delivery_note_jv(self , delivery_note=delivery_note)
            if self.custom_magento_status == 'Cancelled':
                return_sales_invoice(self)
                reverse_journal_entry(self)
                pl_lsts = pick_list_known(self)
                if len(pl_lsts['draft'])!=0:
                    delete_pl_draft(self = self ,draft=pl_lsts['draft'] )
                if len(pl_lsts['submit']) !=0 : 
                    pl_sudimtted(self = self ,submit = pl_lsts['submit'] )
                change_magento_status_to_cancelled(self.custom_magento_id)
            if self.custom_magento_status =='Reorder': 
                cancelled_pick_list(self)
                create_amend_so(self)

def create_amend_so(self): 
    new_so = frappe.copy_doc(self)
    new_so.amended_from = self.name  
    new_so.status = "Draft"   
    new_so.custom_magento_status = "New"
    new_so.name  = None
    new_so.per_delivered = 0 
    new_so.per_billed = 100
    new_so.per_picked =0 
    new_so.insert()
    delivery_date = datetime.now().date()
    for item in new_so.items:
        item.delivery_date = delivery_date
    new_so.payment_schedule = list()
    new_so.delivery_date = delivery_date
    new_so.transaction_date = delivery_date
    new_so.run_method('save')
    new_so.run_method('submit')


def delete_pl_draft(self , draft = list() ):
    for d in draft:
        frappe.delete_doc("Pick List", d)
        
def pl_sudimtted(self ,submit ):
    'check Delivery Note to cancel Pick List or Not '
    dn = frappe.qb.DocType('Delivery Note')
    dni = frappe.qb.DocType('Delivery Note Item')
    exist_dn = (
        frappe.qb.from_(dn)
        .join(dni).on(dn.name == dni.parent)
        .where(dni.against_sales_order == self.name)
        .where(dn.docstatus == 1 )
        .select(dn.name)
        ).run(as_dict = True)
    if len(exist_dn) == 0 : 
        cancelled_pick_list(self)
    else : 
        return_delivery_note(self)
    
        
        
        
def pick_list_known(self): 
    pl = frappe.qb.DocType('Pick List')
    pli = frappe.qb.DocType('Pick List Item')
    pick_list =   (
            frappe.qb.from_(pl)
            .join(pli).on(pl.name == pli.parent)
            .select((pl.docstatus) , 
                    (pl.name) 
                    )
            .where(pli.sales_order == self.name )
            .groupby(pl.name)
        ).run(as_dict=True)
    draft_pl , submitted_pl = list() , list()
    for p in pick_list: 
        if p.docstatus == 0 : 
            draft_pl.append(p.name)
        elif p.docstatus ==1 : 
            submitted_pl.append(p.name)
            
    return {
        'draft' : draft_pl , 
        'submit' : submitted_pl
    }
    
    
            


def create_draft_pick_list(self):
    doc = create_pick_list(self.name)
    use_serial_batch_fields = frappe.db.get_single_value("Stock Settings", "use_serial_batch_fields")
    soi = frappe.qb.DocType('Sales Order Item')
    i = frappe.qb.DocType('Item')
    items = (
        frappe.qb.from_(soi)
        .left_join(i).on(i.name == soi.item_code)
        .select(
            (soi.item_code) , (soi.item_name) , (soi.item_group),
            (soi.description) , (soi.qty) , (soi.stock_qty) , (soi.stock_reserved_qty), 
            (soi.uom) , (soi.conversion_factor) , (soi.stock_uom) ,
            (soi.name.as_('sales_order_item')) 
        )
        .where(i.is_stock_item ==1 )
        .where(soi.parent == self.name)
    ).run(as_dict = True)
    # frappe.throw(str(items))
    doc.locations = list()
    for i in items: 
        row = { 
                    "item_code": i.item_code,
                    "item_name": i.item_name,
                    "description":i.description,
                    "item_group": i.item_group,
                    "qty": i.qty,
                    "stock_qty": i.stock_qty,
                    "stock_reserved_qty": i.stock_reserved_qty,
                    "uom": i.uom,
                    "conversion_factor": i.conversion_factor,
                    "stock_uom":i.stock_uom ,
                    "use_serial_batch_fields": use_serial_batch_fields,
                    "sales_order": self.name,
                    "sales_order_item":i.sales_order_item,
        }
        doc.append('locations' , row)
    doc.save()


@frappe.whitelist()
def stock_entry_method(self):
    allow_to_cerate_stock_entry  , delivery_company , driver = delivery_company_validation(self)
    if allow_to_cerate_stock_entry:
        created = stock_entry_creation(self , delivery_company , driver)
        if created:
            return True

def delivery_company_validation(self):
        if self.custom_magento_status == 'Cancelled':
            frappe.throw(
                'The Sales Order has been cancelled. You cannot pick the items.'
                , title = frappe._('Cancelled Sales Order')
                )
            return False, None , None 
        if self.custom_delivery_company  is None or self.custom_driver is None : 
            frappe.throw(
                'Delivery Company and Driver are not selected in the Sales Order. The Pick List is not ready for Picking.',
                title=frappe._('Missing Delivery Information')
            )
            return False , None , None 
        return True  , self.custom_delivery_company , self.custom_driver 


def stock_entry_creation(self , delivery_company , driver):
    pl = frappe.qb.DocType('Pick List')
    pli = frappe.qb.DocType('Pick List Item')
    so = frappe.qb.DocType(self.doctype)
    soi = frappe.qb.DocType('Sales Order Item')
    pick_list = (
        frappe.qb.from_(pl)
        .join(pli).on(pl.name == pli.parent)
        .select((pl.name).as_('pl_name'))
        .where(pl.docstatus == 1 )
        .where(pli.sales_order == self.name)
        .groupby(pl.name)
        ).run(as_dict = True)
    for loop in pick_list:
        pl_doc = frappe.get_doc('Pick List' , loop.pl_name)
        dict_ = create_stock_entry((pl_doc.as_dict()))
        if bool(dict_) == True and str(dict_) != 'null':
            dict_['stock_entry_type'] = 'Material Transfer'
            for r in dict_['items']:
                warehouse  = (
                    frappe.qb.from_(soi).select((soi.warehouse).as_('target'))
                              .where(soi.item_code == r['item_code'])
                              .where(soi.parent == self.name)
                              ).run(as_dict = True)
                t_warehouse = None 
                if warehouse and warehouse[0] and warehouse[0]['target']:
                    t_warehouse = warehouse[0]['target']
                    
            dict_['to_warehouse'] = t_warehouse
            se_doc = (
                frappe.new_doc('Stock Entry')
                .update(dict_)
                .save()
            )
            for row in se_doc.items:
                row.driver = driver
                row.delivery_company = delivery_company
            se_doc.save().submit()
            return True

@frappe.whitelist()
def create_stock_entry(pick_list):
	validate_item_locations(pick_list)

	if stock_entry_exists(pick_list.get("name")):
		return frappe.msgprint(frappe._("Stock Entry has been already created against this Pick List"))

	stock_entry = frappe.new_doc("Stock Entry")
	stock_entry.pick_list = pick_list.get("name")
	stock_entry.purpose = pick_list.get("purpose")
	stock_entry.set_stock_entry_type()

	if pick_list.get("work_order"):
		stock_entry = update_stock_entry_based_on_work_order(pick_list, stock_entry)
	elif pick_list.get("material_request"):
		stock_entry = update_stock_entry_based_on_material_request(pick_list, stock_entry)
	else:
		stock_entry = update_stock_entry_items_with_no_reference(pick_list, stock_entry)

	stock_entry.set_missing_values()

	return stock_entry.as_dict()

   
########################################################
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
    target.save()
    for item in target.items: 
        item_doc= frappe.get_doc('Item' , item.item_code)
        if item_doc.is_stock_item ==0 :
            target.items.remove(item)
    target.save()
    target.submit()
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
def cancel_stock_reservation_entry(self):
    sre = frappe.qb.DocType('Stock Reservation Entry')
    sre_lst = (frappe.qb.from_(sre).select(sre.name).where(sre.voucher_no == self.name ).where(sre.docstatus ==1 )
               ).run(as_dict = True)
    if len(sre_lst) != 0 : 
        for sre_loop in sre_lst: 
            sre_doc = frappe.get_doc('Stock Reservation Entry' , sre_loop.name)
            sre_doc.run_method('cancel')
def cancelled_pick_list(self): 
    pl = frappe.qb.DocType('Pick List')
    pli = frappe.qb.DocType('Pick List Item')
    se = frappe.qb.DocType('Stock Entry')
    pick_list =   (
            frappe.qb.from_(pl)
            .join(pli).on(pl.name == pli.parent)
            .select(pl.name)
            .where(pli.sales_order == self.name)
            .where(pl.docstatus == 1 )
            .groupby(pl.name)
        ).run(as_dict=True)
    if len(pick_list) != 0: 
            for pl_loop in pick_list:
                stock_entry = (
                    frappe.qb.from_(se).select(se.name)
                    .where(se.pick_list ==pl_loop.name )
                    .where(se.docstatus ==1 )
                ).run(as_dict=True)
                if len(stock_entry) !=0:
                    for se_loop in stock_entry:
                        frappe.db.set_value('Stock Entry' , se_loop.name , 'pick_list' , None)
                cancel_stock_reservation_entry(self)
                pl_doc= frappe.get_doc('Pick List' , pl_loop.name)
                pl_doc.run_method('cancel')
                
                
                
                
def create_empty_cart():
    base_url, headers = base_data("magento")
    url = base_url + "rest/V1/carts/mine"
    
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        order_no = response.text
    else:
        frappe.throw(f"Failed to Create Sales Order in Magento: {str(response.text)}")
        
def add_items_to_cart(self):
    base_url, headers = base_data("magento")
    url = base_url + "/rest/V1/carts/mine/items"
    
    if len(self.items) != 0:
        for item in self.items:
            sku = item.item_code
            name = item.item_name
            qty = item.qty
            price = item.rate
    
            payload = {
                "cartItem":{
                "sku": sku,
                "qty": qty,
                "name": name,
                "price": price,
                "product_type":"simple",
                "quote_id":"842", #order_no
                }
            }
            
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                frappe.msgprint(f"Items Added Successfully to Sales Order", alert = True, indicator = 'green')
            else:
                frappe.throw(f"Failed to Add Items to Sales Order: {str(response.text)}")
        
def add_address_to_cart(self):
    base_url, headers = base_data("magento")
    url = base_url + "/rest/V1/carts/mine/billing-address"
    
    address_sql = frappe.db.sql("""SELECT 
                                        ta.address_line1, 
                                        ta.city, 
                                        ta.country, 
                                        ta.custom_first_name, 
                                        ta.custom_last_name, 
                                        ta.email_id, 
                                        ta.pincode, 
                                        ta.phone 
                                    FROM tabAddress ta
                                    INNER JOIN `tabDynamic Link` tdl ON tdl.parent = ta.name
                                    WHERE tdl.link_doctype = 'Customer' AND tdl.link_name = %s
                                    """, (self.customer), as_dict=True)
    
    if len(address_sql) != 0:
        for address in address_sql:
            street = address.address_line1
            city = address.city
            country = address.country
            counrty_id_sql = frappe.db.sql("SELECT code FROM tabCountry WHERE name = %s" , (country) , as_dict = True)
            if counrty_id_sql and counrty_id_sql[0] and counrty_id_sql[0]['code']:
                country_id = counrty_id_sql[0]['code'] 
            first_name = address.custom_first_name
            last_name = address.custom_last_name
            email_id = address.email_id
            pincode = address.pincode
            phone = address.phone
    else:
        frappe.throw(f"No Address for Customer: {self.customer}")
    
    payload = {
        "address": {
        "city": city,
        "countryId": country_id.upper(),
        "email": email_id,
        "firstname": first_name,
        "lastname": last_name,
        "postcode": pincode,
        "saveInAddressBook": 1,
        "street": [street],
        "telephone": phone
        },
        "useForShipping": True
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        frappe.msgprint(f"Address Added Successfully to Sales Order", alert = True, indicator = 'green')
    else:
        frappe.throw(f"Failed to Add Address to Sales Order: {str(response.text)}")
        
def add_shipping_info(self):
    base_url, headers = base_data("magento")
    url = base_url + "/rest/V1/carts/mine/shipping-information"
    
    payload = {
        "addressInformation": {
        "billingAddress": {
            "city": "Springfield",
            "company": "iprag",
            "email": "customer_email@domain.com",
            "firstname": "Jane",
            "lastname": "Doe",
            "postcode": "335001",
            "region": "UP",
            "street": ["Street"],
            "telephone": "5551234"
        },
        "shippingAddress": {
            "city": "Springfield",
            "company": "iprag",
            "email": "customer_email@domain.com",
            "firstname": "Jane",
            "lastname": "Doe",
            "postcode": "335001",
            "region": "UP",
            "street": ["Street"],
            "telephone": "5551234"
        },
        "shippingCarrierCode": "freeshipping",
        "shippingMethodCode": "freeshipping"
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        frappe.msgprint(f"Shipping Information Added Successfully to Sales Order", alert = True, indicator = 'green')
    else:
        frappe.throw(f"Failed to Add Shipping Information to Sales Order: {str(response.text)}")
                

def place_order(self):
    base_url, headers = base_data("magento")
    url = base_url + "/rest/V1/carts/mine/order"
    
    payload = {
        "paymentMethod":{"method":"checkmo"},
        "shippingMethod":
            {
            "method_code":"freeshipping",

            "carrier_code":"freeshipping",
            "additionalProperties":{}

            }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        json_response = response.json()
        self.custom_magento_id = json_response['message']
        frappe.msgprint(f"Order Placed Successfully to Sales Order", alert = True, indicator = 'green')
    else:
        frappe.throw(f"Failed to Place Order to Sales Order: {str(response.text)}")