import frappe
from frappe.utils import flt



def filter_locations_by_picked_materials_override(locations, picked_item_details) -> list[dict]:
	filterd_locations = []
	precision = frappe.get_precision("Pick List Item", "qty")
	for row in locations:
		key = row.warehouse
		if row.batch_no:
			key = (row.warehouse, row.batch_no)
		print (picked_item_details )
		picked_qty = 0  ################ 
        # picked_item_details.get(key, {}).get("picked_qty", 0)
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