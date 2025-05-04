# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from masar_miraaya.custom.sales_order.sales_order import  cost_of_delivery_jv , create_delivery_company_jv , delivery_note_jv
from masar_miraaya.custom.sales_invoice.sales_invoice import make_gl
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice 
original_gl_entrires = SalesInvoice.make_gl_entries

class RepostSalesOrder(Document):
	@frappe.whitelist()
	def get_sales_orders(self):
		if self.from_date > self.to_date: 
			frappe.throw('From date should be less than to date')
		so = frappe.qb.DocType("Sales Order")
		orders = (
			frappe.qb.from_(so).
			select(
       			(so.name.as_('sales_order')) , 
				(so.customer) , (so.customer_name) , (so.grand_total)
          		)
			.where(so.docstatus == 1 ).where(so.custom_magento_status == 'Delivered').where(so.transaction_date.between(self.from_date  , self.to_date))
		).run(as_dict = True)
		for order in orders:
			self.append('orders',order)
		
  
	@frappe.whitelist()
	def repost_sales_orders(self):
		if len(self.orders) < 25: 
			self.repost()
		else: 
			frappe.enqueue(
				method = self.repost() , 
				self = self , 
    			queue="long",
       			is_async=True
			)
			frappe.msgprint('Reposting has been queued in the background')
	def repost(self):
		if not self.orders:
			frappe.throw('No sales orders to repost')
		if frappe.session.user != 'Administrator':
			frappe.throw('You are not allowed to repost sales orders')
		for order in self.orders:
			sales_order = frappe.get_doc('Sales Order' , order.sales_order)
			self.delete_journal_entries(sales_order)
			cost_of_delivery_jv(self = sales_order)
			create_delivery_company_jv(self = sales_order)
			delivery_note_jv(self  = sales_order)
			self.delete_gl_entries(sales_order.name)
			original_gl_entrires(sales_order)
			si_list = frappe.db.sql(f'''SELECT DISTINCT parent FROM `tabSales Invoice Item` tsii WHERE sales_order  = '{sales_order.name}' ''' , as_dict = True)
			for si in si_list:
				
				make_gl(self = frappe.get_doc('Sales Invoice' , si['parent']))
		frappe.msgprint('Sales Orders have been reposted successfully')
  
	
	def delete_journal_entries(self, sales_order):
		je = frappe.qb.DocType('Journal Entry')
		linked_jv = frappe.qb.from_(je).select(je.name, je.docstatus).where(
			je.custom_reference_doctype == sales_order.name
		).run(as_dict=True)
		def get_linked_jvs(jv_name):
			linked = []
			children = frappe.db.get_all('Journal Entry', filters={
				'amended_from': jv_name
			}, fields=['name', 'docstatus'])
			for child in children:
				linked.append(child)
				linked.extend(get_linked_jvs(child.name)) 
			return linked
		if linked_jv:
			all_jvs_to_delete = []
			for jv in linked_jv:
				all_jvs_to_delete.extend(get_linked_jvs(jv.name))
				all_jvs_to_delete.append(jv)
			for jv_info in reversed(all_jvs_to_delete):
				jv_name = jv_info.name
				docstatus = jv_info.docstatus
				if not frappe.db.exists('Journal Entry', jv_name):
					continue
				if docstatus == 1:
					jv_doc = frappe.get_doc('Journal Entry', jv_name)
					jv_doc.run_method('cancel')  
				frappe.delete_doc('Journal Entry', jv_name)  
    
	def delete_gl_entries(self , sales_order_name):
		gl_entries = frappe.db.sql(f'''SELECT name FROM `tabGL Entry` tge WHERE voucher_type = 'Sales Invoice' AND voucher_no IN (	
					SELECT DISTINCT parent FROM `tabSales Invoice Item` tsii WHERE sales_order  = '{sales_order_name}' ) and is_cancelled  = 0 ''', as_dict=True)
		if len(gl_entries) != 0 : 
			for gl in gl_entries: 
				gl_doc = frappe.db.set_value('GL Entry' , gl.name , 'is_cancelled' , 1)
				
