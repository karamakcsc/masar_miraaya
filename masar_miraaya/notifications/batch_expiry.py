import frappe
from frappe.utils import today, add_months

def near_expiry_batches():
    six_months_later = add_months(today(), 6)
    near_expiry = frappe.get_all(
        "Batch",
        filters={
            "expiry_date": ["between", [today(), six_months_later]],
        },
        fields=["name", "expiry_date"]
    )
    
    for batch in near_expiry:
        doc = frappe.get_doc("Batch", batch.name)
        # doc.run_notification("notify_near_expired_batches")
        doc.run_trigger("notify_near_expired_batches")
        # doc.notify(notification="notify_near_expired_batches")
        