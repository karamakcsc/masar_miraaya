import frappe


@frappe.whitelist()
def get_item(item=None, warehouse=None):
    if item:
        query = frappe.db.sql("""
                            SELECT 
                                tb.item_code, 
                                ti.item_name, 
                                tb.stock_uom, 
                                tb.warehouse, 
                                tsabe.batch_no, 
                                tb.reserved_qty, 
                                tb.actual_qty
                            FROM 
                                tabBin tb 
                            INNER JOIN
                                tabItem ti ON tb.item_code = ti.name
                            INNER JOIN 
                                `tabSerial and Batch Bundle` tsabb ON tb.item_code = tsabb.item_code
                            INNER JOIN
                                `tabSerial and Batch Entry` tsabe ON tsabb.name = tsabe.parent 
                            WHERE tb.item_code = %s
                          """, (item), as_dict=True)
    else:
        query = frappe.db.sql("""
                            SELECT 
                                tb.item_code, 
                                ti.item_name, 
                                tb.stock_uom, 
                                tb.warehouse, 
                                tsabe.batch_no, 
                                tb.reserved_qty, 
                                tb.actual_qty
                            FROM 
                                tabBin tb 
                            LEFT JOIN
                                tabItem ti ON tb.item_code = ti.name
                            LEFT JOIN 
                                `tabSerial and Batch Bundle` tsabb ON tb.item_code = tsabb.item_code
                            LEFT JOIN
                                `tabSerial and Batch Entry` tsabe ON tsabb.name = tsabe.parent 
                          """, as_dict=True)
        
    
    return query