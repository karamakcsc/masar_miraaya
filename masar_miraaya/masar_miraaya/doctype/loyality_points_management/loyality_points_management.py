# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class LoyalityPointsManagement(Document):
	def validate(self):
		self.get_lp_account()
		self.get_accounts_form_company(with_cost_center=False)
	def on_submit(self):
		self.create_journal_entry()

	def get_lp_account(self):
		account_sql = frappe.db.sql("""
			SELECT 
				tpa.account AS customer_account, 
				tpa2.account AS group_account, 
				tc2.default_receivable_account AS company_account
			FROM 
				tabCustomer tc 
			LEFT JOIN 
				`tabParty Account` tpa ON tpa.parent = tc.name
			LEFT JOIN 
				`tabParty Account` tpa2 ON tpa2.parent = tc.customer_group 
			LEFT JOIN 
				tabCompany tc2 ON tc2.name = %s
			WHERE 
				tc.custom_is_loyalty_points = 1 AND tc.name = %s
		""", (self.company, self.loyality_points), as_dict=True)
		
		if  not account_sql:
			frappe.throw("Set Account in one of Customer, Customer Group or Company.", title=_("Missing Account"))

		lp_account = (account_sql[0]['customer_account'] or 
							account_sql[0]['group_account'] or 
							account_sql[0]['company_account'])

		if not lp_account:
			frappe.throw("Set Account in one of Customer, Customer Group or Company.", title=_("Missing Account"))
		self.lp_account = lp_account
		return lp_account

	def get_accounts_form_company(self, with_cost_center=False):
		account = frappe.db.get_value("Company", self.company, ["custom_lp_expense_account", "default_deferred_revenue_account, cost_center"], as_dict=True)
		if with_cost_center == False:
			if account:
				if not account.custom_lp_expense_account:
					frappe.throw(_(f"Set Loyalty Points Expense Account in Company {self.company}"))
				if not account.default_deferred_revenue_account:
					frappe.throw(_(f"Set Deferred Revenue Account in Company {self.company}"))
				self.lp_expense_account = account.custom_lp_expense_account
				self.deferred_revenue_account = account.default_deferred_revenue_account
		if with_cost_center == True:
			if account.cost_center:
				return account.cost_center
		
	def create_journal_entry(self):
		lp_expense_account = self.lp_expense_account
		lp_account = self.lp_account
		deferred_revenue_account = self.deferred_revenue_account
		cost_center = self.get_accounts_form_company(with_cost_center=True)
		party_type = "Customer"
		party = self.loyality_points  #### 
		user_remarks = self.user_remarks
		dimension_account = self.customer ####
		
		if self.transaction_type == "Addition": 		# If order is delivered in Magento
				debit_account = lp_expense_account
				credit_account = lp_account
				debit_amount = float(self.amount)
				credit_amount = float(self.amount)
		elif self.transaction_type == "Deduction":			# If order is canceled in Magento
			debit_account = deferred_revenue_account
			credit_account = lp_account
			debit_amount = float(self.amount)
			credit_amount = float(self.amount)
		
		jv = frappe.new_doc("Journal Entry")
		jv.posting_date = self.posting_date
		jv.company = self.company
		jv.voucher_type = "Journal Entry"
		jv.custom_reference_document = self.doctype
		jv.custom_reference_doctype = self.name
		debit_accounts = {
					"account": debit_account,
					"debit_in_account_currency": debit_amount,
					"debit" : debit_amount,
					"cost_center": cost_center,
					"customer": dimension_account,
					"user_remark": user_remarks
					}
		debit_account_doc = frappe.get_doc('Account' ,debit_account )
		if debit_account_doc.account_type in ['Receivable', 'Payable']:
			debit_accounts["party_type"] = party_type
			debit_accounts["party"] = party
		credit_accounts = {
					"account": credit_account,
					"credit_in_account_currency": credit_amount,
					"credit" :credit_amount,
					"cost_center": cost_center,
					"customer": dimension_account,
					"user_remark": user_remarks
					
				}
		creadit_account_doc = frappe.get_doc('Account' ,credit_account )
		if creadit_account_doc.account_type in ['Receivable', 'Payable']:
			credit_accounts["party_type"] = party_type
			credit_accounts["party"] = party
		jv.append("accounts", debit_accounts)
		jv.append("accounts", credit_accounts)
		
		jv.save(ignore_permissions=True)
		jv.submit()
		frappe.msgprint("Journal Entry has been Created Successfully.", alert=True, indicator='green')