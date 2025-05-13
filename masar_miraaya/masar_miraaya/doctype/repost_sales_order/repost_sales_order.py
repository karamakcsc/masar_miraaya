# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from masar_miraaya.custom.sales_order.sales_order import (
    cost_of_delivery_jv,
    create_delivery_company_jv,
    delivery_note_jv,
    reverse_journal_entry,
    return_sales_invoice,
    deferred_revenue_account,
)
from masar_miraaya.custom.sales_invoice.sales_invoice import set_return_account , on_submit
from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice
from datetime import datetime, timedelta, time
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice

class RepostSalesOrder(Document):
    @frappe.whitelist()
    def get_sales_orders(self):
        if self.from_date > self.to_date:
            frappe.throw("From date should be less than to date") 
        so = frappe.qb.DocType("Sales Order")
        orders = (
            frappe.qb.from_(so)
            .select(so.name.as_("sales_order"), so.customer, so.customer_name, so.grand_total)
            .where((so.docstatus == 1) & (so.custom_magento_status == self.status))
            .where(so.transaction_date.between(self.from_date, self.to_date))
            .orderby(so.transaction_date)
        ).run(as_dict=True)
        self.orders = []
        for order in orders:
            self.append("orders", order)
    # def handle_return_delivery_notes(self, sales_order):
    #         if sales_order.custom_magento_status != "Delivered":
    #             return
    #         delivery_notes = frappe.db.get_all(
    #             "Delivery Note",
    #             filters={"against_sales_order": sales_order.name, "is_return": 1},
    #             fields=["name", "docstatus"]
    #         )
    #         for dn in delivery_notes:
    #             dn_doc = frappe.get_doc("Delivery Note", dn.name)
    #             if dn_doc.docstatus == 1:
    #                 dn_doc.cancel()
    #             frappe.delete_doc("Delivery Note", dn_doc.name)
    #             print(f"Return Delivery Note {dn_doc.name} has been canceled and deleted.")
    @frappe.whitelist()
    def repost_sales_orders(self):
        if not self.orders:
            frappe.throw("No sales orders to repost")

        if frappe.session.user != "Administrator":
            frappe.throw("You are not allowed to repost sales orders")

        frappe.enqueue(self.repost, queue="long" , timeout=10000)

        frappe.msgprint("Reposting sales orders in progress ...", alert=True, indicator="blue")         
    def repost(self):
        if not self.orders:
            frappe.throw("No sales orders to repost")
        for order in self.orders:
                sales_order = frappe.get_doc("Sales Order", order.sales_order)
                self.delete_journal_entries(sales_order)
                linked_dn = frappe.db.get_all(
                    "Delivery Note Item",
                    filters={"against_sales_order": sales_order.name},
                    fields=["DISTINCT parent"],
                )
                if linked_dn:
                    cost_of_delivery_jv(self=sales_order)
                    create_delivery_company_jv(self=sales_order)
                    delivery_note_jv(self=sales_order)
                if sales_order.custom_magento_status in ["Cancelled" , "Reorder"]:
                    reverse_journal_entry(self=sales_order)
                self.repost_sales_invoices(sales_order)
                if not frappe.db.exists("Sales Invoice Item", {"docstatus": ["!=", 2], "sales_order": sales_order.name}):
                    if sales_order.custom_magento_status in ["Delivered", "Cancelled" , "Reorder"]:
                        create_new_invoice(sales_order)
                        if sales_order.custom_magento_status in  ["Cancelled" , "Reorder"]:
                            return_sales_invoice(sales_order)
                    else:
                        frappe.throw(f"Sales Order {sales_order.name} has invalid status: {sales_order.custom_magento_status}")
                frappe.msgprint(f"Sales Order {sales_order.name} has been reposted successfully.", alert=True, indicator="green")
                
    def repost_sales_invoices(self, sales_order):
        si_list = frappe.db.sql(
            """
            SELECT DISTINCT sii.parent
            FROM `tabSales Invoice Item` sii
            JOIN `tabSales Invoice` si ON si.name = sii.parent
            WHERE sii.sales_order = %s AND si.return_against IS NULL
            ORDER BY si.modified DESC
            """,
            sales_order.name,
            as_dict=True,
        )
        self.delete_gl_entries(sales_order_name = sales_order.name)
        for re in si_list:
            original_name = re["parent"]
            return_invoices = frappe.get_all("Sales Invoice", filters={"return_against": original_name}, pluck="name")
            for return_inv in return_invoices:
                return_doc = frappe.get_doc("Sales Invoice", return_inv)
                if return_doc.docstatus == 1:
                    return_doc.cancel()
                if sales_order.custom_magento_status == "Delivered":
                    frappe.delete_doc("Sales Invoice", return_doc.name)
            si_doc = frappe.get_doc("Sales Invoice", original_name)
            frappe.db.set_value("Sales Invoice", si_doc.name, "docstatus", 0)
            si_doc.reload()
            si_doc.docstatus = 0
            si_doc.set_posting_time = 1
            si_doc.posting_date =  sales_order.transaction_date
            si_doc.due_date = sales_order.transaction_date
            for item in si_doc.items:
                item.service_start_date = sales_order.transaction_date
                item.service_end_date = sales_order.transaction_date
            si_doc.payment_schedule = []
            si_doc.save()
            si_doc.submit()
            if sales_order.custom_magento_status in  ["Cancelled" , "Reorder"]:
                for return_inv in return_invoices:
                    frappe.db.set_value("Sales Invoice", return_doc.name, "docstatus", 0)
                    frappe.db.set_value("Sales Invoice", return_doc.name, "amended_from", "")
                    new_return = frappe.get_doc("Sales Invoice", return_inv)
                    new_return.docstatus = 0
                    new_return.set_posting_time = 1
                    if isinstance(si_doc.posting_time, timedelta):
                        total_seconds = int(si_doc.posting_time.total_seconds())
                        hours, remainder = divmod(total_seconds, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        posting_time_obj = time(hour=hours, minute=minutes, second=seconds)
                    elif isinstance(si_doc.posting_time, str):
                        posting_time_obj = datetime.strptime(si_doc.posting_time, "%H:%M:%S").time()
                    else:
                        posting_time_obj = si_doc.posting_time 
                    original_dt = datetime.combine(si_doc.posting_date, posting_time_obj)
                    new_dt = original_dt + timedelta(hours=1)
                    new_return.posting_date = new_dt.date()
                    new_return.due_date = new_dt.date()
                    new_return.posting_time = new_dt.time()
                    new_return.payment_schedule = []
                    set_return_account(self = new_return)
                    for item in new_return.items:
                        item.service_start_date = item.service_end_date = new_dt.date()
                    new_return.save()
                    
                    new_return.submit()              
        print(f"Return Order {sales_order.name} has been created and submitted.")
    def delete_journal_entries(self, sales_order):
        """Delete all Journal Entries linked to a Sales Order."""
        je = frappe.qb.DocType("Journal Entry")
        linked_jvs = (
            frappe.qb.from_(je)
            .select(je.name, je.docstatus)
            .where(je.custom_reference_doctype == sales_order.name)
        ).run(as_dict=True)
        def get_all_linked_jvs(jv_name):
            children = frappe.db.get_all("Journal Entry", filters={"amended_from": jv_name}, fields=["name", "docstatus"])
            result = []
            for child in children:
                result.append(child)
                result.extend(get_all_linked_jvs(child.name))
            return result
        all_jvs = []
        for jv in linked_jvs:
            all_jvs.extend(get_all_linked_jvs(jv.name))
            all_jvs.append(jv)
        for jv in reversed(all_jvs):
            if not frappe.db.exists("Journal Entry", jv.name):
                continue
            if jv.docstatus == 1:
                frappe.get_doc("Journal Entry", jv.name).cancel()
            frappe.delete_doc("Journal Entry", jv.name)
    def delete_gl_entries(self, sales_order_name):
        """Delete all GL Entries linked to a Sales Order."""
        gl_entries = frappe.db.sql(
            """
            SELECT name FROM `tabGL Entry`
            WHERE voucher_type = 'Sales Invoice'
              AND is_cancelled = 0
              AND voucher_no IN (
                SELECT DISTINCT parent FROM `tabSales Invoice Item`
                WHERE sales_order = %s
              )
            """,
            sales_order_name,
            as_dict=True,
        )
        for gl in gl_entries:
            frappe.db.set_value("GL Entry", gl.name, "is_cancelled", 1)

def create_new_invoice(sales_order):
    """Create a new Sales Invoice for a Sales Order."""
    deferred_acc = deferred_revenue_account(company=sales_order.company)
    if not deferred_acc:
        frappe.throw(
            f"Set Default Deferred Revenue Account in Company {frappe.utils.get_link_to_form('Company', sales_order.company)}"
        )
    
    si = frappe.qb.DocType("Sales Invoice")
    sii = frappe.qb.DocType("Sales Invoice Item")
    existing_invoices = (
        frappe.qb.from_(si)
        .join(sii).on(si.name == sii.parent)
        .where(sii.sales_order == sales_order.name)
        .select(si.name, si.docstatus)
        .run(as_dict=True)
    )
    
    if not existing_invoices:
        doc = make_sales_invoice(sales_order.name)
        set_invoice_dates(doc, sales_order.transaction_date, deferred_acc)
        doc.save()
        doc.submit()
        frappe.msgprint(f"Sales Invoice {doc.name} has been created and submitted.", alert=True, indicator="green")
    else:
        existing = existing_invoices[0]
        if existing["docstatus"] == 1:
            frappe.msgprint(f"Sales Invoice {existing['name']} already created and submitted.", alert=True, indicator="blue")
        elif existing["docstatus"] == 2:
            doc = make_sales_invoice(sales_order.name)
            set_invoice_dates(doc, sales_order.transaction_date, deferred_acc)
            doc.save()
            doc.submit()
            frappe.msgprint(f"Sales Invoice {existing['name']} was cancelled. New Invoice has been created.", alert=True, indicator="orange")


def set_invoice_dates(invoice_doc, date, deferred_acc):
    invoice_doc.set_posting_time = 1
    invoice_doc.posting_date = invoice_doc.due_date = date
    for item in invoice_doc.items:
        item.enable_deferred_revenue = 1
        item.deferred_revenue_account = deferred_acc
        item.service_start_date = item.service_end_date = date
        if item.qty == 0:
            item.qty = frappe.db.get_value("Sales Order Item", item.so_detail, "qty")