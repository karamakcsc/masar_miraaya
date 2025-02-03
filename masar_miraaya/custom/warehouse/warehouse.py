import frappe 
from masar_miraaya.api import get_packed_warehouse
def validate(self , method):
    is_packed_wh(self)
 
def is_packed_wh(self): 
    if self.custom_is_packed_wh: 
        exist_packed_wh = get_packed_warehouse()
        if len(exist_packed_wh) != 0 and  exist_packed_wh[0] and exist_packed_wh[0]['name']: 
            frappe.throw('Only One Packed Warehouse is allowed. Existing Warehouse: <b>{wh}</b>'.format(wh=exist_packed_wh[0]['name']))
        