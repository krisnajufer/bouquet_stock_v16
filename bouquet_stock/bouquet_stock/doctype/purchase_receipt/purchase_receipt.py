# Copyright (c) 2026, Krisna Jufer and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PurchaseReceipt(Document):
	pass

@frappe.whitelist()
def filter_material_code(doctype, txt, searchfield, start, page_len, filters):
	PO = frappe.qb.DocType("Purchase Order")
	POM = frappe.qb.DocType("Purchase Order Materials")

	txt = f"%{txt}%"
	result = (
		frappe.qb.select(
			POM.material_code.as_("value"),
			POM.material_name,
			PO.name,
			(POM.qty - POM.accepted_qty).as_("remaining_accepted")
		)
		.from_(PO)
		.left_join(POM)
		.on(PO.name == POM.parent)
		.where(
			(PO.docstatus == 1)
			& (PO.name == filters.get("purchase_order"))
			& (POM.accepted_qty < POM.qty)
			& (POM.percentage_accepted_qty < 99.99)
		)
		.where(
			POM.material_code.like(txt)
			| POM.material_name.like(txt)
		)
	).run()

	return result

# @frappe.whitelist()
# def set_po_material()