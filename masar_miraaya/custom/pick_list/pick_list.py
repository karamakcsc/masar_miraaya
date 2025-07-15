import frappe
from erpnext.stock.doctype.pick_list.pick_list import  PickList
import json
from masar_miraaya.api import change_magento_status_to_fullfilled , get_packed_warehouse 
from erpnext.stock.doctype.stock_reservation_entry.stock_reservation_entry import get_available_qty_to_reserve
from frappe.query_builder.functions import  Sum
from frappe.utils import flt
from collections import defaultdict

def on_submit(self , method):
    sales_invoice_validation(self)
    items_validation(self)
    qty_validation(self)
    assigned_to_validate(self)
    user_vaildation(self)
    
    
def sales_invoice_validation(self):
    for ref in self.locations:
        si = frappe.qb.DocType('Sales Invoice')
        soi = frappe.qb.DocType('Sales Invoice Item')
        query = (
            frappe.qb.from_(si)
            .join(soi).on(si.name == soi.parent)
            .select(
                (si.name).as_('si_name'),
            )
            .where(soi.sales_order == ref.sales_order)
            .where(si.docstatus == 1)
            .groupby(si.name)
        ).run(as_dict = True)
        if len(query) != 0:
            for row in query:
                if row.si_name:
                    return 1
                else:
                    frappe.throw(str(f"Please create a Sales Invoice for the Sales Order {ref.sales_order} before proceeding with the Pick List."))
        else:
            frappe.throw(str(f"Please create a Sales Invoice for the Sales Order {ref.sales_order} before proceeding with the Pick List."))
    
def items_validation(self):
    linked_so = get_linked_so(self)
    soi = frappe.qb.DocType('Sales Order Item')
    i =  frappe.qb.DocType('Item')
    for so in linked_so:
        if so.so_name:
            sql = (
                    frappe.qb.from_(soi)
                    .join(i)
                    .on(soi.item_code == i.name)
                    .select(
                        (i.name).as_('item_code'),
                            (soi.name).as_('row_id'), (soi.idx))
                    .where(soi.parent == so.so_name)
                    .where(i.is_stock_item ==1 )
                    ).run(as_dict = True)
            item_lst = [loop.item_code for loop in sql]
            row_lst = [loop.row_id for loop in sql]
            for location in self.locations:
                if location.item_code not in item_lst: # or location.sales_order_item not in row_lst:
                    frappe.throw(
                        'The item {item} is currently part of a sales order and must be picked along with other items.'
                        .format(item = location.item_code), 
                        title=frappe._('Item Pickup Notice')
                    )
            items_lst = list()
            for l in self.locations: 
                items_lst.append(l.sales_order_item)
            for r in sql:
                if r.row_id not in items_lst:
                    frappe.throw(
                        'Item {item} at index {idx} in the Sales Order is missing or not found.'
                        .format(item = r.item_code , idx=r.idx),
                        title=frappe._('Sales Order Item Missing')
                    )
def qty_validation(self): 
    linked_so = get_linked_so(self)
    soi = frappe.qb.DocType('Sales Order Item')
    i =  frappe.qb.DocType('Item')
    pli = frappe.qb.DocType('Pick List Item')
    for so in linked_so:
        if so.so_name:
            items = (
                    frappe.qb.from_(soi)
                    .join(i).on(soi.item_code == i.name)
                    .select(
                        (i.name) , 
                        Sum(soi.qty).as_('qty') , 
                    )
                    .where(soi.parent == so.so_name)
                    .where(i.is_stock_item ==1 )
                    .groupby(soi.item_code)
                    ).run(as_dict = True)
            for item in items: 
                qty = (frappe.qb.from_(pli)
                    .select(Sum(pli.qty).as_('qty')
                            , Sum(soi.picked_qty).as_('picked_qty'))
                    .where(pli.parent == self.name)
                    .where(pli.item_code == item.name)
                    .groupby(pli.item_code)
                ).run(as_dict = True)[0]
                if qty['qty'] != item.qty or qty['picked_qty'] != item.qty:
                    
                    frappe.throw(
                        '''The quantity for item {item} does not match the sales order quantity, 
                        or the picked quantity does not match the sales order quantity. 
                        Both quantities must be equal.'''
                        .format(item = item.name),
                    title=frappe._('Quantity Mismatch Error')
                    )      
        
def assigned_to_validate(self): 
    if frappe.session.user == 'Administrator':
        return True
    if self.custom_assigned_to is None: 
        frappe.throw(
            '''Please ensure that you click the "Assign To Me" button before submitting. 
            This step is necessary to assign this pick to yourself.''', 
            title = frappe._('Assign Validation')
        )
@frappe.whitelist()
def user_vaildation(self):
    if frappe.session.user == 'Administrator':
        return True
    if frappe.session.user != self.custom_assigned_to: 
        frappe.throw(
                'Pick List is already assigned to {assigned_to}. You cannot assign this request to yourself.'
                .format(assigned_to=self.custom_assigned_to), 
                title=frappe._('Assigned to Another User')
            )
        return False
    return True 
@frappe.whitelist()
def packing(self):
    self = frappe._dict(json.loads(self))##
    linked_so = get_linked_so(self)##
    pack_wh = get_packed_wh()
    if pack_wh:
        se_list = create_stock_transfar(
                self = self , 
                sales_order = linked_so , 
                target_wh = pack_wh )
        create_stock_reservation_entries(
                self= frappe.get_doc(self.doctype , self.name) ,
                stock_entry_list = se_list , 
                warehouse = pack_wh
            )
        error , continue_ = change_magento_status(linked_so)############# Magento
        if continue_: ############# Magento      
            change_so_status(linked_so)      
            frappe.db.set_value(self.doctype , self.name , 'custom_packed' ,1)
            return 1 
        else : ############# Magento
            frappe.throw('Error Magento Connection : {error}'.format(error = str(error))) ############# Magento
            
@frappe.whitelist()
def miraaya_packing(self):
    self = frappe._dict(json.loads(self))##
    linked_so = get_linked_so(self)##
    pack_wh = get_packed_wh()
    if pack_wh:
        se_list = create_stock_transfar(
                self = self , 
                sales_order = linked_so , 
                target_wh = pack_wh )
        create_stock_reservation_entries(
                self= frappe.get_doc(self.doctype , self.name) ,
                stock_entry_list = se_list , 
                warehouse = pack_wh
            )
        change_so_status(linked_so)
        frappe.db.set_value(self.doctype , self.name , 'custom_packed' ,1)

def change_magento_status(linked_so): 
    text = 'Magento ID is None or Sales Order is Not Submitted.' 
    for so in linked_so:
        so_doc = frappe.get_doc('Sales Order' , so.so_name)
        if so_doc.docstatus == 1 and so_doc.custom_magento_id is not None:  
            text , status_code = change_magento_status_to_fullfilled(so_doc.custom_magento_id)
            if status_code  in [200 , 201]:
                return  text , True
    return text , False

def change_so_status(linked_so):
    if len(linked_so) != 0 : 
        for so in linked_so:
            so_doc = frappe.get_doc('Sales Order' , so.so_name)
            if so_doc.docstatus == 1:
                so_doc.custom_magento_status = 'Fullfilled'
                so_doc.save(ignore_permissions=True)

def get_linked_so(self):
    pl = frappe.qb.DocType(self.doctype)
    pli = frappe.qb.DocType('Pick List Item')
    linked_so = (
        frappe.qb.from_(pl)
        .join(pli).on(pl.name == pli.parent)
        .select((pli.sales_order).as_('so_name'))
        .where(pl.name == self.name)
        .groupby(pli.sales_order)
    ).run(as_dict = True)
    return linked_so
                
@frappe.whitelist()
def assign_to_me(self):
    self = frappe._dict(json.loads(self))
    user = frappe.session.user
    role = frappe.get_roles(user)
    if user == 'Administrator':
        return 
    if 'Picker' not in role:
            frappe.throw(
                'User {user} does not have the "Picker" role assigned and therefore cannot be assigned the Stock Entry.'
                .format(user = user),
                title = frappe._('Role Validation')
                )
            return None
    if self.custom_assigned_to is not None : 
            frappe.throw(
                'The Material Request is already assigned to {assigned_to}. You cannot assign this request to yourself.'
                .format(assigned_to=self.custom_assigned_to), 
                title=frappe._('Assigned to Another User')
            )
            return None 
    frappe.db.set_value(self.doctype, self.name, "custom_assigned_to", user)
    frappe.db.set_value(self.doctype, self.name, "custom_assigned", 1)
    frappe.db.commit()
    return user


@frappe.whitelist()
def user_validation_picker(self):
    if frappe.session.user == 'Administrator':
        return True
    self = frappe.get_doc(json.loads(self))
    if not self.custom_assigned_to:
        frappe.throw(
            'The Pick list is not assigned. Please assign it to yourself.',
            title=frappe._('Assigned to Yourself')
        )
        return False
    if frappe.session.user != self.custom_assigned_to:
        frappe.throw(
            'Pick List is already assigned to {assigned_to}. You cannot assign this request to yourself.'.format(
                assigned_to=self.custom_assigned_to
            ),
            title=frappe._('Assigned to Another User')
        )
        return False
    return True

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
    

def get_packed_wh(): 
    exist_wh = get_packed_warehouse()
    if len(exist_wh) == 0: 
        frappe.throw('A packed warehouse must be specified. No packed warehouse found.')
        return None 
    return exist_wh[0]['name']

def create_stock_transfar(self, sales_order, target_wh): 
    _type = 'Material Transfer'
    cost_center = get_cost_center(self=self)
    se_list = list()

    grouped_items = defaultdict(lambda: {"qty": 0, "details": None})
    for l in self.locations:
        key = (l['item_code'], l['warehouse']) 
        if not grouped_items[key]["details"]:
            grouped_items[key]["details"] = l
        grouped_items[key]["qty"] += l['qty']

    for so in sales_order: 
        data = {
            "stock_entry_type": _type,
            "pick_list": self.name,
            "purpose": _type, 
            "to_warehouse": target_wh,
        }
        items = []

        for (item_code, s_warehouse), value in grouped_items.items():
            l = value["details"]
            items.append({ 
                "s_warehouse": s_warehouse,
                "t_warehouse": target_wh,
                "item_code": item_code, 
                "item_name": l['item_name'],
                "description": l['description'],
                "item_group": l['item_group'],
                "qty": value["qty"],
                "cost_center": cost_center,
                "allow_zero_valuation_rate": 1
            })

        data['items'] = items
        se_doc = frappe.new_doc('Stock Entry').update(data).save().submit()
        se_list.append(se_doc)

    return se_list
            


def create_stock_reservation_entries(self, stock_entry_list, warehouse):
    if len(stock_entry_list) == 0:
        return

    for location in self.locations:
        if not (location.sales_order and location.sales_order_item):
            continue

        is_stock_item, has_serial_no, has_batch_no = frappe.get_cached_value(
            "Item", location.item_code, ["is_stock_item", "has_serial_no", "has_batch_no"]
        )

        if not is_stock_item:
            continue

        qty_to_reserve = flt(location.picked_qty) - flt(location.stock_reserved_qty)
        if qty_to_reserve <= 0:
            continue

        available_qty = get_available_qty_to_reserve(location.item_code, warehouse)

       
        delivered_qty = get_delivered_qty(location.sales_order_item)
        already_reserved_qty = get_reserved_qty(location.sales_order_item)

    
        allowed_qty = min(
            available_qty,
            flt(location.stock_qty) - delivered_qty - already_reserved_qty
        )

        if allowed_qty <= 0:
            continue  

        item_data = {
            "item_code": location.item_code,
            "warehouse": warehouse,
            "voucher_type": "Sales Order",
            "has_serial_no": has_serial_no,
            "has_batch_no": has_batch_no,
            "voucher_no": location.sales_order,
            "voucher_detail_no": location.sales_order_item,
            "from_voucher_type": self.doctype,
            "from_voucher_no": self.name,
            "from_voucher_detail_no": location.name,
            "qty_to_reserve": qty_to_reserve,
            "available_qty": available_qty,
            "voucher_qty": location.stock_qty,
            "company": self.company,
            "stock_uom": location.stock_uom,
            "reserved_qty": min(qty_to_reserve, allowed_qty)
        }

        frappe.new_doc('Stock Reservation Entry').update(item_data).save().submit()
        
def get_delivered_qty(sales_order_item):
 
    return flt(frappe.db.sql("""
        SELECT SUM(qty) FROM `tabDelivery Note Item`
        WHERE so_detail = %s AND docstatus = 1
    """, (sales_order_item,), as_list=1)[0][0] or 0)

def get_reserved_qty(sales_order_item):

    return flt(frappe.db.sql("""
        SELECT SUM(reserved_qty) FROM `tabStock Reservation Entry`
        WHERE voucher_detail_no = %s AND docstatus = 1
    """, (sales_order_item,), as_list=1)[0][0] or 0)
