# Copyright (c) 2024, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DriverPicklist(Document):
	def validate(self):
		self.html_table()

	def html_table(self):
		location_sql = frappe.db.sql("""
								SELECT DISTINCT 
        							til.area, til.`column`, til.`row`, til.box_no, tpai.item_code, 
									tpai.item_name, tpai.qty
        						FROM 
              						`tabPicking Area` tpa 
								INNER JOIN 
        							`tabPicking Area Item` tpai ON tpai.parent = tpa.name
								LEFT JOIN 
        							`tabItem Location` til ON tpai.location = til.name
								WHERE 
        							tpa.sales_order = %s 
               						AND tpa.driver = %s 
                     				AND tpa.docstatus = 1
                               """, (self.sales_order, self.driver), as_dict=True)

		
		
		style = """
			<style>
				.wide-table { width: 100%; }
				.column { width: 14%;}
			</style>
		"""
		html = """  <div class="container mt-3">"""
		html+= """      <table class="table table-bordered table-hover wide-table">"""
		html+= """          <thead class="thead-light"> """
		html+= """              <tr> """
		html+= """                  <th scope="col" class="column">Item Code</th>"""
		html+= """                  <th scope="col" class="column">Item Name</th>"""
		html+= """                  <th scope="col" class="column">Qty</th> """
		html+= """                  <th scope="col" class="column">Location</th> """
		html+= """                  <th scope="col" class="column">Column</th> """
		html+= """                  <th scope="col" class="column">Row</th> """
		html+= """                  <th scope="col" class="column">Box No.</th> """
		html+= """              </tr> """ 
		html+= """          </thead> """
		html += "           <tbody>"
  
		
		for loc in location_sql:
			html += "           <tr>"
			html += f"              <td> {loc['item_code']} </td>"
			html += f"""            <td> {loc['item_name']} </td> """
			html += f"""            <td> {loc['qty']} </td> """
			html += f"""            <td> {loc['area'] or ''} </td> """
			html += f"""            <td> {loc['column'] or ''} </td> """
			html += f"""            <td> {loc ['row'] or ''} </td> """
			html += f"""            <td> {loc['box_no'] or ''} </td> """
			html += "           </tr>"
		html += "           </tbody>"
		html += """     </table>
					</div>"""
		code = style + html
		self.editor = code 