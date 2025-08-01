import frappe
from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice , make_delivery_note , update_status , create_pick_list
from erpnext.controllers.sales_and_purchase_return import make_return_doc
from erpnext.accounts.doctype.journal_entry.journal_entry import make_reverse_journal_entry
import json
from erpnext.stock.doctype.pick_list.pick_list import ( 
                validate_item_locations,     stock_entry_exists ,   update_stock_entry_based_on_work_order,
                update_stock_entry_based_on_material_request ,update_stock_entry_items_with_no_reference )
from masar_miraaya.api import change_magento_status_to_cancelled , get_customer_wallet_balance
from datetime import datetime
from masar_miraaya.api import base_data , create_magento_auth_webhook , request_with_history
from masar_miraaya.custom.pick_list.pick_list import get_packed_wh , create_stock_reservation_entries
from datetime import timedelta
@frappe.whitelist()
def get_payment_channel_amount(child):
    payment_chnnel_amount = 0 
    for row in json.loads(child):
        payment_chnnel_amount += float(row.get('amount') if ( row.get('amount') and row.get('amount') is not None ) else 0 )
    return payment_chnnel_amount

def validate(self, method):
    cash_and_payment_channel_validate(self)
    validation_payment_channel_amount(self)


def wallet_balance_validation(self):
    customer_doc = frappe.get_doc('Customer' , self.customer)
    wallet_balance = get_customer_wallet_balance(customer_id=self.customer , magento_id=customer_doc.custom_customer_id)
    if wallet_balance is None:
        frappe.throw(
            f'Please Check if Customer {str(self.customer)} is Publish to Magento.'
        )
    for channel in self.custom_payment_channels:
        if channel.channel:
            doc = frappe.get_doc('Customer' ,channel.channel)
            if doc.custom_is_digital_wallet:
                if channel.amount > float(wallet_balance):
                    frappe.throw(
                    f"""The Customer has a Wallet Balance of {wallet_balance}, 
                    but the Amount Specified in The Channel ({channel.channel})Exceeds the Available Balance
                    Please Ensure That The Amount Does Not Exceed The Wallet Balance."""
                  )
        
def cash_and_payment_channel_validate(self):
    if not self.custom_total_amount:
        frappe.throw("Please set the cash on delivery amount or payment channel amount.")
    if self.custom_cash_on_delivery_amount is not None: 
        if float(self.custom_cash_on_delivery_amount) > 0 and float(self.custom_is_cash_on_delivery) == 0: 
                frappe.throw(f" Cash on Delivery Amount is {self.custom_cash_on_delivery_amount} so Is Cash on Delivery must be checked")
    if (
            (
            ( float(self.custom_payment_channel_amount)  if self.custom_payment_channel_amount else 0 )
            +
            (float(self.custom_cash_on_delivery_amount) if self.custom_cash_on_delivery_amount else 0 )
        ) != float(self.custom_total_amount)
    ):
        frappe.throw(f"""
                     Total Amount Must be Equal to Cash on Delivery Amount and Payment Channel Amount. 
                     Cash on Delivery Amount : {self.custom_cash_on_delivery_amount}  
                     Payment Chaannel Amount: { self.custom_payment_channel_amount}
                     So Total Amount must be {
                        ( self.custom_payment_channel_amount  if self.custom_payment_channel_amount else 0 )
                        +
                        (self.custom_cash_on_delivery_amount if self.custom_cash_on_delivery_amount else 0 )} 
                    Not {self.custom_total_amount}""")
        

def validation_payment_channel_amount(self):
    if self.custom_total_amount is None or self.grand_total is None:
        frappe.throw(
            'Total amount or grand total is missing. Please ensure both values are provided.',
            title=frappe._("Validation Error")
        )
        
    if abs(float(self.custom_total_amount) - float(self.grand_total) ) > 0.001 :
        frappe.throw(
            f'The total amount for the item must match the total amount for the payment channels with Cash on Delivery.'
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

def get_account(company , customer ): 
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
        if account is None: 
            company_doc = frappe.get_doc('Company' , company) 
            account = company_doc.default_receivable_account if company_doc.default_receivable_account else None 
        if account is None:
            frappe.throw('Payment Channel {pc_name} Not Have Receivable Account or Define a Defulat Account in Group {pc_group} or in Company {comp}'
                        .format(
                            pc_name = frappe.utils.get_link_to_form("Customer", customer),
                            pc_group =frappe.utils.get_link_to_form("Customer Group", pc_doc.customer_group),
                            comp = frappe.utils.get_link_to_form("Company", company) 
                        )
                        , title = frappe._('Missing Account')
                        )
        return account 

def get_cost_center(self):
        if hasattr(self , 'cost_center') and self.cost_center: 
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
            doc.set_posting_time = 1
            doc.posting_date = self.transaction_date  # 2024-12-21
            doc.due_date = self.transaction_date
            
            for item in doc.items: 
                if self.custom_manually == 0:
                    item.enable_deferred_revenue = 1 
                    item.deferred_revenue_account = deferred_revenue_acc
                    item.service_start_date = self.transaction_date
                    item.service_end_date = self.transaction_date
                else: 
                    item.enable_deferred_revenue = 0
                    item.deferred_revenue_account = None
                    item.service_start_date = None
                    item.service_end_date = None
                if item.qty == 0: 
                    item.qty = frappe.db.get_value('Sales Order Item' , item.so_detail , 'qty')
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
    if self.custom_manually == 0:
        wallet_balance_validation(self)
        cont =  create_draft_pick_list(self)
        if cont : 
            create_sales_invoice(self)
        if self.amended_from is not None : 
            magento_id , entity_id ,address_id = magento_reorder(self)
            self.custom_magento_id = magento_id
            frappe.db.set_value(self.doctype , self.name , 'custom_magento_id' , magento_id)
            fleetroot_reorder(self , magento_id , entity_id , address_id)
            wallet_debit_reorder(self , magento_id)
        frappe.db.set_value(self.doctype , self.name , 'custom_stock_entry' , 0, update_modified=False )
    elif self.custom_manually == 1: 
        cont =  create_draft_pick_list(self)
        if cont : 
            create_sales_invoice(self)
    
def digital_wallet_account(customer_id , company): 
    account  = None   
    if customer_id : 
        cust_doc = frappe.get_doc('Customer' , customer_id)
        for c in cust_doc.accounts: 
            if c.account: 
                account = c.account
                break
        if account is None: 
            group_doc = frappe.get_doc('Customer Group' , cust_doc.customer_group)
            for g in group_doc.accounts: 
                if g.account: 
                    account = g.account
                    break
        if account is None: 
            company_doc = frappe.get_doc('Company' , company)
            account = company_doc.default_receivable_account
        if account is None : 
            frappe.throw("Set Account in one of Digital Wallet, Digital Wallet Group or Company.", title=_("Missing Account"))
        else: 
            return account
        

def on_update_after_submit(self, method):
        if  self.docstatus == 1 and self.custom_manually == 0:
            if self.custom_magento_status == 'On the Way':
                validate_pick_list(self)
                delete_previous_jv(self)
                cost_of_delivery_jv(self)
                create_delivery_company_jv(self)
                if self.custom_stock_entry == 0 : 
                    stock_entry_method(self)
                    self.custom_stock_entry =1 
                    frappe.db.set_value(self.doctype , self.name , 'custom_stock_entry' , 1 , update_modified=False )
            if self.custom_magento_status == 'Delivered':
                validate_pick_list(self)
                stock_entry_validation(self)
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
                change_magento_status_to_cancelled(self.name ,self.custom_magento_id)
            if self.custom_magento_status =='Reorder':
                cancelled_pick_list(self)
                create_amend_so(self)
            

def create_amend_so(self): 
    new_so = frappe.copy_doc(self )
    new_so.amended_from = self.name  
    new_so.status = "Draft"   
    new_so.custom_magento_status = "New"
    new_so.name  = None
    new_so.per_delivered = 0 
    new_so.per_billed = 0
    new_so.billing_status =  "Not Billed"
    new_so.per_picked =0 
    delivery_date = datetime.now().date()
    for item in new_so.items:
        item.delivery_date = delivery_date
        item.picked_qty = 0 
    new_so.payment_schedule = list()
    new_so.delivery_date = delivery_date
    new_so.transaction_date = delivery_date
    new_so.custom_magento_id = None
    remove_discount(new_so , discount = self.discount_amount)
    new_so.custom_stock_entry = 0
    new_so.run_method('save')
    return new_so

def remove_discount(self , discount):
    if self.discount_amount : 
        new_cash_on_delivery_amount = (
            (float(self.custom_cash_on_delivery_amount) if self.custom_cash_on_delivery_amount else 0 )
            +
            (float(discount) if discount else 0 )
        )
        self.discount_amount = 0
        self.custom_is_cash_on_delivery =1 
        self.custom_cash_on_delivery_amount = new_cash_on_delivery_amount
        self.custom_total_amount = new_cash_on_delivery_amount + float(self.custom_payment_channel_amount if self.custom_payment_channel_amount else 0 )
        self.save()

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
    
def stock_entry_validation(self): 
    pli = frappe.qb.DocType('Pick List Item')
    se = frappe.qb.DocType('Stock Entry')
    pick_list = (
            frappe.qb.from_(pli)
            .select(pli.parent)
            .where(pli.sales_order == self.name)
            .groupby(pli.parent).run(as_dict = True)        
    )
    if len(pick_list) == 0 : 
        frappe.throw('Please ensure the order is properly packed before proceeding with delivery.')
    stock_entry = (
            frappe.qb.from_(se)
            .select(se.name)
            .where(se.docstatus == 1 )
            .where(se.pick_list.isin([p.parent for p in pick_list]))
        ).run(as_dict = True)
    # if len(stock_entry) == 0: 
    #     frappe.throw('Please ensure the order is packed and the stock entry is created before proceeding with delivery.')
    

        
        
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
    
    
def validate_pick_list(self):
    pl = frappe.qb.DocType('Pick List')
    pli = frappe.qb.DocType('Pick List Item')
    query = (
        frappe.qb.from_(pl)
        .join(pli).on(pl.name == pli.parent)
        .select(pl.name, pl.custom_packed)
        .where(pli.sales_order == self.name)
        .where(pl.docstatus == 1) 
        .groupby(pl.name)
    ).run(as_dict=True)
    
    if len(query) != 0:
        for p in query:
            if p.custom_packed:
                return 0
            else:
                frappe.throw(f"Please ensure the Pick List {p.name} is fullfilled before change on the way or delivered.")
    else:
        frappe.throw(str("Please ensure the Pick List is fullfilled before change on the way or delivered."))


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
    doc.custom_delivery_date = self.delivery_date
    doc.custom_delivery_time = self.custom_delivery_time
    doc.custom_magento_id = self.custom_magento_id
    if len(doc.locations) != 0 :
        try:
            doc.save()
            return True
        except Exception as e:
            return False 
    return False


@frappe.whitelist()
def stock_entry_method(self):
    allow_to_cerate_stock_entry  , delivery_company , driver = delivery_company_validation(self)
    if allow_to_cerate_stock_entry:
        cancel_stock_reservation_entry(self)
        cont = outing_se_existing(self)
        if cont:
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

def outing_se_existing(self): 
    delivery_wh = delivery_warehouse()
    sql = get_existing_se(self = self , warehouse = delivery_wh )
    if len(sql) !=0 : 
        return False
    return True
    
def stock_entry_creation(self , delivery_company , driver):
    packed_wh  , delivery_wh = get_packed_wh() , delivery_warehouse()
    exist = get_existing_se(self)
    if len(exist) != 0 : 
        for s in exist: 
            se_doc = frappe.get_doc('Stock Entry' , s.name)
            se_doc.to_warehouse = delivery_wh
            for item in se_doc.items: 
                item.s_warehouse  , item.t_warehouse = packed_wh ,  delivery_wh 
                item.driver = driver 
                item.delivery_company = delivery_company
                item.serial_and_batch_bundle = None
            new_se = frappe.new_doc('Stock Entry').update(se_doc.as_dict()).save().submit()
            create_stock_reservation_entry( self , new_se ,delivery_wh )
            
def get_existing_se(self , warehouse = None ):
    se  , pli = frappe.qb.DocType('Stock Entry') , frappe.qb.DocType('Pick List Item')
    exist = (
        frappe.qb.from_(se)
        .select(se.name)
        .left_join(pli)
        .on(pli.parent == se.pick_list)
        .where(pli.sales_order == self.name)
        .groupby(se.name)
    )
    if warehouse: 
        exist = exist.where(se.to_warehouse == warehouse)
    return exist.run(as_dict = True)

def create_stock_reservation_entry( self , new_se , warehouse ):
    picklist = frappe.get_doc('Pick List' , new_se.pick_list)
    create_stock_reservation_entries(self= picklist ,  stock_entry_list=[new_se] , warehouse= warehouse)

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
        item.delivery_company = self.custom_delivery_company
        item.driver = self.custom_driver
    target.save()
    target.submit()
    return target.name

def delivery_note_jv(self , delivery_note = None ):
    if delivery_note is not None: 
        delivery_note = frappe.get_doc('Delivery Note' ,delivery_note )
    company_doc = frappe.get_doc("Company", self.company)
    sales_account = company_doc.default_income_account
    revenue_account =deferred_revenue_account(company=self.company)
    cost_center = get_cost_center(self)
    total =  float(self.total)
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
            'debit_in_account_currency' :total,
            'debit' :total,
            'cost_center': cost_center,
        }
    jv.append("accounts", dr_row)
    cr_row = { 
                'account' : sales_account, 
                'credit_in_account_currency' :total,
                'credit' : total, 
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
    pli = frappe.qb.DocType('Pick List Item')
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
            ##### Return the item to box 
            for i in doc.items:
                warehouse = (
                   frappe.qb.from_(pli).select(pli.warehouse)
                   .where(pli.item_code == i.item_code)
                   .where(pli.sales_order == i.against_sales_order)
                   ).run(as_dict = True)
                if warehouse and warehouse[0] and  warehouse[0]['warehouse']: 
                    i.warehouse = warehouse[0]['warehouse']
            #### End Return item to box
            if doc : 
                doc.save().submit()
    
def reverse_journal_entry(self):
    linked_dn = frappe.db.get_all(
                    "Delivery Note Item",
                    filters={"against_sales_order": self.name},
                    fields=["DISTINCT parent"],
                )
    if len(linked_dn) ==0 :
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

def delete_previous_jv(self): 
    je = frappe.qb.DocType('Journal Entry')
    linked_jv = frappe.qb.from_(je).select(je.name , je.docstatus).where(je.custom_reference_doctype == self.name).run(as_dict = True)
    if len(linked_jv) != 0 : 
        for jv in linked_jv: 
            if jv.docstatus == 1 : 
                jv_doc = frappe.get_doc('Journal Entry' , jv.name)
                jv_doc.run_method('cancel')
            frappe.delete_doc('Journal Entry',jv.name)
            
def cost_of_delivery_jv(self):
    company_doc = frappe.get_doc('Company' , self.company)
    dc_doc = frappe.get_doc('Customer' , self.custom_delivery_company)
    cost_center = get_cost_center(self)
    cr_account = get_account(company=self.company , customer=self.custom_delivery_company )
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
    if delivery_cost in [None]:
        frappe.throw('Set Delivary Cost of Delivery Company {dc}.'
                     .format(dc = frappe.utils.get_link_to_form("Customer", self.custom_delivery_company))
                     , 
                     title = frappe._("Missing Delivery Cost")
        )
    if delivery_cost not in [0 , None]:
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
                    .orderby(se.modified , order=frappe.qb.desc)
                ).run(as_dict=True)
                cancel_stock_reservation_entry(self)
                if len(stock_entry) !=0:
                    for se_loop in stock_entry:
                        if self.custom_magento_status == 'Reorder':
                            frappe.db.set_value('Stock Entry' , se_loop.name , 'pick_list' , None)
                        else:
                            se_doc = frappe.get_doc('Stock Entry' , se_loop.name)
                            se_doc.run_method('cancel')
                
                pl_doc= frappe.get_doc('Pick List' , pl_loop.name)
                pl_doc.run_method('cancel')
                
def get_address(self):
    if self.customer_address:
        address_sql = frappe.db.sql("""
            SELECT ta.address_line1, ta.city,ta.country, ta.custom_first_name, 
                ta.custom_last_name, ta.email_id, ta.pincode, ta.phone 
                FROM tabAddress ta
                WHERE ta.name = %s
        """, (self.customer_address), as_dict=True)
        if len(address_sql) != 0:
            address = address_sql[0]
            street = address.address_line1
            city = address.city
            country = address.country
            counrty_id_sql = frappe.db.sql("SELECT code FROM tabCountry WHERE name = %s" , (country) , as_dict = True)
            if counrty_id_sql and counrty_id_sql[0] and counrty_id_sql[0]['code']:
                country_id = counrty_id_sql[0]['code'].upper()
            first_name = address.custom_first_name
            last_name = address.custom_last_name
            email_id = address.email_id
            pincode = address.pincode
            phone = address.phone
            address_dict = {
                "country_id": country_id,"street": [street],
                "postcode": pincode,"city": city,"firstname": first_name,
                "lastname": last_name,"email": email_id, "telephone": phone
            }
            return address_dict
        return None
    else:
            frappe.throw(f"Add  Address to Customer: {self.customer} , in Sales order.")

def combine_date_time(self):
    if self.delivery_date and self.custom_delivery_time:
        date = datetime.strptime(self.delivery_date, "%Y-%m-%d")
        time = datetime.strptime(self.custom_delivery_time, "%H:%M:%S").time()
        date_time = datetime.combine(date, time).replace(microsecond=0) 
        return date_time
    else:
        frappe.throw("Please Set Delivery Date and Delivery Time.")
    
    
    
    
          
def magento_reorder(self):
    customer_doc = frappe.get_doc('Customer' , self.customer)
    base_url, headers = base_data(request_in="magento_customer_auth" , customer_email=customer_doc.custom_email)
    customer_id = customer_doc.custom_customer_id
    cart_id = create_empty_cart(self , base_url , headers)
    continue_ = add_items_to_cart(self, cart_id ,  base_url , headers)
    address = get_address(self)
    if continue_:
        address_id = add_address_to_cart(self , address,base_url,headers)
        add_shipping_info(self , address,base_url,headers)
        entity_id = set_payment_info(self , address , base_url, headers)
        if entity_id:
            magento_id = get_magento_id(self, customer_id, entity_id , base_url, headers)
            frappe.msgprint('Magento reordered successfully' ,
                alert=True, 
                indicator='green'
            )
            return magento_id   , entity_id , address_id
def create_empty_cart(self , base_url , headers):
    url = base_url + "rest/V1/carts/mine"
    response = request_with_history(
                    req_method='POST', 
                    document=self.doctype, 
                    doctype=self.name, 
                    url=url, 
                    headers=headers     
                )
    if response.status_code == 200:
        cart_id = response.text
        return cart_id
    else:
        frappe.throw(f"Failed to Create Sales Order in Magento: {str(response.text)}")
        
def add_items_to_cart(self, cart_id ,  base_url , headers):
    url = base_url + "rest/V1/carts/mine/items"
    if len(self.items) != 0:
        for item in self.items:
            sku = item.item_code
            qty = item.qty
            item_doc = frappe.get_doc("Item", sku)
            if item_doc.is_stock_item:
                payload = { "cartItem":{"sku": sku,"qty": qty,"quote_id": cart_id,}}
                response = request_with_history(
                    req_method='POST', 
                    document=self.doctype, 
                    doctype=self.name, 
                    url=url, 
                    headers=headers  ,
                    payload=payload        
                )
                if response.status_code not in [200 , 201]:
                    frappe.throw(f"Failed to Add Items to Sales Order: {str(response.text)}")
                    return False
        return True
    else: 
        return False

def add_address_to_cart(self , address , base_url , headers ):
    url = base_url + "rest/V1/carts/mine/billing-address"
    payload = {"address": address}
    response = request_with_history(
                    req_method='POST', 
                    document=self.doctype, 
                    doctype=self.name, 
                    url=url, 
                    headers=headers  ,
                    payload=payload        
                )
    if response.status_code not in [200 , 201]:
            frappe.throw(f"Failed to Add Address to Sales Order 'Billing Address': {str(response.text)}") 
    else: 
        return   response.text
        
def add_shipping_info(self , address,base_url,headers):
    url = base_url + "rest/V1/carts/mine/shipping-information"
    if address:
        payload = {
        "addressInformation": {
            "shipping_address": address,"billing_address": address,
            "shipping_carrier_code": "flatrate","shipping_method_code": "flatrate"
            }
        }
        response = request_with_history(
                    req_method='POST', 
                    document=self.doctype, 
                    doctype=self.name, 
                    url=url, 
                    headers=headers  ,
                    payload=payload        
                )
        if response.status_code != 200:
            frappe.throw(f"Failed to Add Address to Sales Order 'Shipping Addresss': {str(response.text)}")   
        return True
    else: 
        frappe.throw(f'Error To Get Address Data."Shipping Addresss": {str(response.text)}')

def set_payment_info(self , address , base_url, headers):
    url = base_url + "rest/default/V1/carts/mine/payment-information"
    date_time = combine_date_time(self)
    payload = {
        "paymentMethod": {
            "method": "cashondelivery"
        },
        "billing_address": address,
        "extension_attributes": {
            "preferred_delivery_date": str(date_time)
        }
    }
    response =request_with_history(
                    req_method='POST', 
                    document=self.doctype, 
                    doctype=self.name, 
                    url=url, 
                    headers=headers  ,
                    payload=payload        
                )
    if response.status_code in [200 , 201]:
        entity_id = response.text
        return entity_id
    else:
        frappe.throw(f"Error Adding Shipping Information to Sales Order : {str(response.text)}" )
        return None
        
    

def get_magento_id(self, customer_id, entity_id , base_url, headers):
    url = base_url + f"rest/V1/orders?searchCriteria[filterGroups][0][filters][0][field]=customer_id&searchCriteria[filterGroups][0][filters][0][value]={customer_id}&searchCriteria[filterGroups][0][filters][0][field]=entity_id&searchCriteria[filterGroups][0][filters][0][value]={entity_id}&searchCriteria[filterGroups][0][filters][0][conditionType]=eq"
    setting = frappe.get_doc('Magento Setting')
    auth = create_magento_auth_webhook()
    headers['Authorization'] = f"Bearer {auth}"
    response = request_with_history(
                    req_method='GET', 
                    document=self.doctype, 
                    doctype=self.name, 
                    url=url, 
                    headers=headers     
                )
    json_response = response.json()
    if response.status_code in [200 , 201]:        
        for increment_id in json_response['items']:
            magento_id = increment_id['increment_id']
            return magento_id
    else:
        frappe.throw(f"Error Getting Magento ID: {str(json_response)} <br> url:{str(url)} <br> headers:{str(headers)}" )
            
def get_items_details(self):
    items = list()
    fees_shipping = 0 
    for i in self.items:
        item_doc = frappe.get_doc('Item', i.item_code)
        if item_doc.is_stock_item == 0 : 
            fees_shipping += (i.amount if i.amount else 0 )
        else : 
            items.append(
            {
                "item": i.item_code,
                "price": str(i.rate),
                "qty": str(i.qty),
                "tax": "0",
                "total":str(i.rate*i.qty)
                }
            ) 
    return  items ,  fees_shipping
    
        
def fleetroot_reorder(self , magento_id , entity_id , address_id):
    base_url , headers = base_data("webhook")
    setting = frappe.get_doc("Magento Setting")
    if setting.auth_type == "Develop":
        env = "dev"
    elif setting.auth_type == "Production":
        env = "prod"
    url = base_url + f'/order/save-order-and-track/{env}'
    coupon_amount = self.discount_amount if self.discount_amount else 0 
    items ,  fees_shipping = get_items_details(self)
    total_amount = self.total - fees_shipping # Order Total - Shipping Fess
    order_details = {
        "address_id" : address_id,
        "coupon_amount": coupon_amount, 
        "delivery_slot": "10 am - 4 pm",
        "expected_delivery_date" : str(combine_date_time(self)),
        "order_id": magento_id,
        "entity_id": entity_id,
        "due_amount": str(self.custom_cash_on_delivery_amount if self.custom_cash_on_delivery_amount else 0 ) , 
        "paid_amount": str(self.custom_payment_channel_amount if self.custom_payment_channel_amount else 0 ) , 
        "payment_method" : "cashondelivery" if (self.custom_payment_channel_amount  in [None , 0 ]) else "prepaid",
        "shipping_fee": fees_shipping,
        "total_amount" : total_amount,
        "wallet_amount_used": str(self.custom_payment_channel_amount if self.custom_payment_channel_amount else 0 ) # Wallet Amount
    } 
    pickup = {
        "lat": "33.2793535","lng": "44.3867075","address": "Jadryah 915 | 26 | 3","stop_type": 1, "note": "pickup point",
        "datetime": str(combine_date_time(self)),"contact_name": "Miraaya","contact_phone": "+964 780 699 9197", 
        "contact_email": "dev@miraaya.com", "order_no" : magento_id,
        "payment_mode": "cashondelivey", "total_amount": self.custom_total_amount,
        "items":items
    }
    customer_doc = frappe.get_doc('Customer' ,self.customer )
    
    delivery = {
        "lat": "33.3152832", "lng": "44.3661671",
        "address": self.customer_address , "stop_type": 2,  "note": "delivery point", 
        "datetime": str(combine_date_time(self)),
        "contact_name": self.customer_name,
        "contact_phone": self.contact_phone, 
        "contact_email":customer_doc.custom_email,
        "order_no":magento_id,
        "payment_mode":"cashondelivery" if (self.custom_payment_channel_amount not in [None , 0 ]) else "prepaid",
        "total_amount": self.custom_total_amount,
        "priority": 2,
        "qr_code":magento_id,
        "items":items
    }
    tracking_details_obj = {
        "name": f"Miraaya{magento_id}",
        "description": f"Miraaya Order tracking, Order ID: {magento_id}",
        "driver_id": "","driver_code": "",
        "auto_assignment": 1,
        "pickup":pickup,
        "delivery":delivery
    }
    tracking_details = {
        "order_status": "processing",
        "entity_id": entity_id,
        "order_id": magento_id,
        "sales_order_id": self.name, 
        "obj": tracking_details_obj
    }
    payload = {
        "orderDetails": order_details, 
        "trackingDetails": tracking_details,
    }
    response =request_with_history(
                    req_method='POST', 
                    document=self.doctype, 
                    doctype=self.name, 
                    url=url, 
                    headers=headers  ,
                    payload=payload        
                )
    if response.status_code in [200 , 201]:
        frappe.msgprint('fleetroot reordered successfully' ,
                alert=True, 
                indicator='green'
            )
    else:
        frappe.throw(f"Error Saving reorder to fleetroot: {str(response.text)}")


def wallet_debit_reorder(self , magento_id=None):
    for ph in self.custom_payment_channels:
        cust_doc = frappe.get_doc('Customer' , ph.channel)
        if (cust_doc is not None) and (cust_doc.custom_is_digital_wallet ==1):
            data = {
                'customer' : self.customer , 
                'transaction_type' : 'Adjustment',
                'digital_wallet' : ph.channel,
                'wallet_adjustment_account':digital_wallet_account(ph.channel , self.company),
                'action_type' : 'Debit',
                'adjustment_amount' : ph.amount,
                'user_remarks' : 'Debit Amount {amount} From Reorder Number ERP:{so_name} , Magento ID : {magento_id}'
                                .format(amount = ph.amount , so_name = self.name , magento_id = magento_id), 
            }
            
            wallet_doc = frappe.new_doc('Wallet Top-up')
            wallet_doc.update(data)
            wallet_doc.save()
            wallet_doc.submit()
            frappe.msgprint('Wallet Top Up Created Successfully.' ,        
                    alert=True, 
                    indicator='green' 
            )