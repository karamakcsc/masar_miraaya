import frappe


@frappe.whitelist()
def get_items(item=None, warehouse=None):
    conditions = " 1=1 "

    if item:
        conditions += f" AND tb.item_code = '{item}' "
    
    if warehouse:
        conditions += f" AND tb.warehouse = '{warehouse}' "

    query = frappe.db.sql(f"""
        SELECT 
            tb.item_code, 
            ti.item_name, 
            tb.stock_uom, 
            tb.warehouse, 
            tb2.name,
            tb2.batch_qty,
            tb2.expiry_date, 
            tb.reserved_qty, 
            tb.actual_qty,
            ti.image,
            ti.disabled,
            ti.custom_magento_disabled
        FROM 
            tabBin tb 
        INNER JOIN
            tabItem ti ON tb.item_code = ti.name
        INNER JOIN 
            `tabBatch` tb2 ON tb.item_code = tb2.item
        WHERE 
            {conditions}
    """, as_dict=True)

    return query
