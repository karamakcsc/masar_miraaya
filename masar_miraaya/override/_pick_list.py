import frappe
from frappe.utils import flt
from frappe.model.document import Document
from erpnext.stock.doctype.pick_list.pick_list import get_available_item_locations, get_items_with_location_and_quantity
from frappe import _
from frappe.utils.nestedset import get_descendants_of

def filter_locations_by_picked_materials_override(locations, picked_item_details) -> list[dict]:
	filterd_locations = []
	precision = frappe.get_precision("Pick List Item", "qty")
	for row in locations:
		key = row.warehouse
		if row.batch_no:
			key = (row.warehouse, row.batch_no)
		picked_qty = 0  ################ 
		picked_item_details.get(key, {}).get("picked_qty", 0)
		if not picked_qty:
			filterd_locations.append(row)
			continue
		if picked_qty > row.qty:
			row.qty = 0
			picked_item_details[key]["picked_qty"] -= row.qty
		else:
			row.qty -= picked_qty
			picked_item_details[key]["picked_qty"] = 0.0
			if row.serial_nos:
				row.serial_nos = list(set(row.serial_nos) - set(picked_item_details[key].get("serial_no")))

		if flt(row.qty, precision) > 0:
			filterd_locations.append(row)
	return filterd_locations


class PickListOverride(Document):
	@frappe.whitelist()
	def set_item_locations_override(self, save=False):
		self.validate_for_qty()
		items = self.aggregate_item_qty()
		picked_items_details = self.get_picked_items_details(items)
		self.item_location_map = frappe._dict()
		mc_warehouse = [wh.name for wh in frappe.db.sql("""SELECT name from `tabWarehouse` tw WHERE  tw.name LIKE("%MC%") AND tw.is_group =0 """, as_dict=True)]
		not_mc_warehouse = frappe.db.sql("""SELECT name from `tabWarehouse` tw WHERE  tw.name NOT LIKE("%MC%") AND tw.is_group =0 """, as_dict=True)
		from_warehouses = [self.parent_warehouse] if self.parent_warehouse else []
		if self.parent_warehouse:
			from_warehouses.extend(get_descendants_of("Warehouse", self.parent_warehouse))
		else:
			from_warehouses = [w.name for w in not_mc_warehouse]
		# Create replica before resetting, to handle empty table on update after submit.
		
		locations_replica = self.get("locations")
		for wh in from_warehouses:
			if wh  in mc_warehouse:
				from_warehouses.remove(wh)
		# reset
		reset_rows = []
		for row in self.get("locations"):
			if not row.picked_qty:
				reset_rows.append(row)

		for row in reset_rows:
			self.remove(row)
		updated_locations = frappe._dict()
		len_idx = len(self.get("locations")) or 0
		for item_doc in items:
			item_code = item_doc.item_code

			self.item_location_map.setdefault(
				item_code,
				get_available_item_locations(
					item_code,
					from_warehouses,
					self.item_count_map.get(item_code),
					self.company,
					picked_item_details=picked_items_details.get(item_code),
					consider_rejected_warehouses=self.consider_rejected_warehouses,
				),
			)

			locations = get_items_with_location_and_quantity(item_doc, self.item_location_map, self.docstatus)

			item_doc.idx = None
			item_doc.name = None

			for row in locations:
				location = item_doc.as_dict()
				location.update(row)
				key = (
					location.item_code,
					location.warehouse,
					location.uom,
					location.batch_no,
					location.serial_no,
					location.sales_order_item or location.material_request_item,
				)

				if key not in updated_locations:
					updated_locations.setdefault(key, location)
				else:
					updated_locations[key].qty += location.qty
					updated_locations[key].stock_qty += location.stock_qty

		for location in updated_locations.values():
			if location.picked_qty > location.stock_qty:
				location.picked_qty = location.stock_qty

			len_idx += 1
			location.idx = len_idx
			self.append("locations", location)

		# If table is empty on update after submit, set stock_qty, picked_qty to 0 so that indicator is red
		# and give feedback to the user. This is to avoid empty Pick Lists.
		if not self.get("locations") and self.docstatus == 1:
			for location in locations_replica:
				location.stock_qty = 0
				location.picked_qty = 0

				len_idx += 1
				location.idx = len_idx
				self.append("locations", location)

			frappe.msgprint(
				_(
					"Please Restock Items and Update the Pick List to continue. To discontinue, cancel the Pick List."
				),
				title=_("Out of Stock"),
				indicator="red",
			)

		if save:
			self.save()