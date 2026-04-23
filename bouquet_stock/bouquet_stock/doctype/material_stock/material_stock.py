# Copyright (c) 2026, Krisna Jufer and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MaterialStock(Document):
	pass

@frappe.whitelist()
def get_critical_stock():
	MS = frappe.qb.DocType("Material Stock")
	is_critical_stock_alert = frappe.db.get_single_value("Stock Settings", "is_critical_stock_alert")
	result = (
		frappe.qb.select(
			MS.material_code,
			MS.material_name,
			MS.actual_qty,
			MS.safety_stock,
			MS.min_qty,
			MS.max_qty,
		)
		.from_(MS)
		.where(
			MS.actual_qty <= MS.min_qty
		)
	).run(as_dict=True)

	
	return {
		"result": result,
		"is_critical_stock_alert": is_critical_stock_alert
	}