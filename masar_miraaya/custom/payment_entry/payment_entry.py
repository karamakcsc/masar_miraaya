import frappe
import json


@frappe.whitelist()
def get_magento_id(pe_doc):
    pe_doc = frappe._dict(json.loads(pe_doc))
    result = []

    if pe_doc:
        # pe_doc = frappe.get_doc("Payment Entry", pe_doc)
        if pe_doc['references']:
            for ref in pe_doc['references']:
                if ref['reference_name']:
                    id_sql = frappe.db.sql(f"""
                        SELECT 
                            IFNULL(custom_reference_document, '') AS custom_reference_document,
                            IFNULL(custom_reference_doctype, '') AS custom_reference_doctype
                        FROM `tab{ref['reference_doctype']}`
                        WHERE name = %s
                    """, (ref['reference_name'],), as_dict=True)

                    if len(id_sql) > 0:
                        id_sql = id_sql[0]
                        if id_sql.custom_reference_doctype and id_sql.custom_reference_document:
                            so_doc = frappe.get_doc(id_sql.custom_reference_document, id_sql.custom_reference_doctype)
                            if so_doc.custom_magento_id:
                                result.append({
                                    "reference_name": ref['reference_name'],
                                    "custom_magento_id": so_doc.custom_magento_id
                                })
    return result