import frappe
from frappe.utils import flt
from frappe.model.document import Document
from erpnext.stock.doctype.pick_list.pick_list import (
	get_available_item_locations,
	get_items_with_location_and_quantity,
)
from frappe import _
from frappe.utils.nestedset import get_descendants_of
from frappe.query_builder import Case

def filter_locations_by_picked_materials_override(locations, picked_item_details) -> list[dict]:
	filtered_locations = []
	precision = frappe.get_precision("Pick List Item", "qty")

	for row in locations:
		key = row.warehouse
		if row.batch_no:
			key = (row.warehouse, row.batch_no)	
		picked_qty = picked_item_details.get(key, {}).get("picked_qty", 0)

		if not picked_qty:
			filtered_locations.append(row)
			continue

		if picked_qty > row.qty:
			picked_item_details[key]["picked_qty"] -= row.qty
			row.qty = 0
		else:
			row.qty -= picked_qty
			picked_item_details[key]["picked_qty"] = 0.0
			if row.serial_nos:
				row.serial_nos = list(
					set(row.serial_nos) - set(picked_item_details[key].get("serial_no", []))
				)

		if flt(row.qty, precision) > 0:
			filtered_locations.append(row)
	return filtered_locations


class PickListOverride(Document):
	@frappe.whitelist()
	def set_item_locations_override(self, save=False):
		self.validate_for_qty()
		items = self.aggregate_item_qty()
		picked_items_details = self.get_picked_items_details(items)

		if not hasattr(self, "item_count_map"):
			self.item_count_map = {}

		self.item_location_map = frappe._dict()

		# Get warehouses
		mc_warehouses = [wh.name for wh in frappe.db.sql("""
			SELECT name FROM `tabWarehouse` 
			WHERE name LIKE "%MC%" AND is_group = 0
		""", as_dict=True)]

		non_mc_warehouses = [
			wh.name for wh in frappe.db.sql("""
				SELECT name FROM `tabWarehouse` 
				WHERE name NOT LIKE "%MC%" AND is_group = 0
			""", as_dict=True)
		]

		from_warehouses = [self.parent_warehouse] if self.parent_warehouse else non_mc_warehouses

		if self.parent_warehouse:
			from_warehouses.extend(get_descendants_of("Warehouse", self.parent_warehouse))

		# Exclude MC warehouses
		from_warehouses = [wh for wh in from_warehouses if wh not in mc_warehouses]

		# Keep backup of current locations
		locations_replica = self.get("locations")

		# Remove unpicked rows
		reset_rows = [row for row in self.get("locations") if not row.picked_qty]
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

			locations = get_items_with_location_and_quantity(
				item_doc, self.item_location_map, self.docstatus
			)

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
					updated_locations[key] = location
				else:
					updated_locations[key].qty += location.qty
					updated_locations[key].stock_qty += location.stock_qty

		for location in updated_locations.values():
			if (location.get("picked_qty") or 0) > location.get("stock_qty", 0):
				location["picked_qty"] = location["stock_qty"]

			len_idx += 1
			location["idx"] = len_idx
			self.append("locations", location)

		# If no locations left, restore dummy rows for visual red indicator
		if not self.get("locations") and self.docstatus == 1:
			for location in locations_replica:
				location.stock_qty = 0
				location.picked_qty = 0
				len_idx += 1
				location.idx = len_idx
				self.append("locations", location)

			frappe.msgprint(
				_(
					"Please Restock Items and Update the Pick List to continue. "
					"To discontinue, cancel the Pick List."
				),
				title=_("Out of Stock"),
				indicator="red",
			)

		if save:
			self.save()

	def _get_pick_list_items_override(self, items):
		pi = frappe.qb.DocType("Pick List")
		pi_item = frappe.qb.DocType("Pick List Item")
		query = (
			frappe.qb.from_(pi)
			.inner_join(pi_item)
			.on(pi.name == pi_item.parent)
			.select(
				pi_item.item_code,
				pi_item.warehouse,
				pi_item.batch_no,
				pi_item.serial_and_batch_bundle,
				pi_item.serial_no,
				(Case().when(pi_item.picked_qty > 0, pi_item.picked_qty).else_(pi_item.stock_qty)).as_(
					"picked_qty"
				),
			)
			.where(
				(pi_item.item_code.isin([x.item_code for x in items]))
				& ((pi_item.picked_qty > 0) | (pi_item.stock_qty > 0))
				& (pi.status != "Completed")
				& (pi.status != "Cancelled")
				& (pi_item.docstatus != 2)
				& (pi.name == self.name)
			)
		)

		if self.name:
			query = query.where(pi_item.parent != self.name)
		print(query)
		query = query.for_update()

		return query.run(as_dict=True)