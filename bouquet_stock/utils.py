import frappe
from datetime import (
	date,
	time
)

from frappe.query_builder.functions import ( 
	Sum, 
	Coalesce
)

def get_actual_qty(material_code : str):
    return frappe.db.get_value("Material Stock", {"material_code": material_code}, "actual_qty")

def get_min_max_calculation(max_qty : float, avg_qty : float, lead_time : float):
    safety_stock = max((max_qty - avg_qty) * lead_time, 0) or 0
    min_qty = avg_qty * lead_time + safety_stock or 0
    max_qty_stock = min_qty * 2 or 0

    return frappe._dict({
        "safety_stock": safety_stock,
        "min_qty": min_qty,
        "max_qty": max_qty_stock,
    })

def calculate_sle_by_period(material_code:list, posting_date:date, posting_time:time):

	SLE = frappe.qb.DocType("Stock Ledger Entry")

	date_condition = (
		(SLE.posting_date < posting_date) |
		((SLE.posting_date == posting_date) & (SLE.posting_time <= posting_time))
	)

	result = (
		frappe.qb.from_(SLE)
		.select(SLE.material_code, Sum(SLE.qty_change).as_("last_qty_change"))
		.where(
			(SLE.material_code.isin(material_code)) &
			date_condition &
			(SLE.is_cancelled == 0)
		)
        .groupby(
            SLE.material_code
        )
		.run(as_dict=True)
	)

	return result