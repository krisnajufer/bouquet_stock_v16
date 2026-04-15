# Copyright (c) 2026, Krisna Jufer and contributors
# For license information, please see license.txt

import frappe

from frappe.utils import flt

from frappe.model.document import Document
from bouquet_stock.bouquet_stock.doctype.stock_ledger_entry.stock_ledger_entry import (
	make_sle,
	cancel_sle
)

class PurchaseReceipt(Document):
	def validate(self):
		self.validate_materials_qty()

	def on_submit(self):
		self.process_stock_ledger_entries()
		self.update_purchase_order_items()
		
	def on_cancel(self):
		self.process_stock_ledger_entries(True)
		self.update_purchase_order_items()

	def validate_materials_qty(self):
		msg = []
		for row in self.materials:
			if row.ordered_qty < (row.accepted_qty + row.qty):
				msg.append(f"Material <b>{row.material_name}</b> di Pemesanan <b>{row.purchase_order}</b>, qty diterima melebihi dari qty yang dipesan !!")
		if msg:
			msg = "<br>".join(msg)
			frappe.throw(msg)

	def process_stock_ledger_entries(self, cancelled=False):
		for child in self.materials:
			if cancelled:
				cancel_sle(self, child)
			else:
				make_sle(self, child)


	def update_purchase_order_items(self):
		po_map = {}

		# --- 1. Tentukan multiplier (untuk cancel) ---
		multiplier = -1 if self.docstatus == 2 else 1

		# --- 2. Group PR items ---
		for row in self.materials:
			if not row.purchase_order or not row.po_detail:
				continue

			key = (row.purchase_order, row.po_detail)
			po_map.setdefault(key, 0)
			po_map[key] += flt(row.qty) * multiplier

		if not po_map:
			return

		# --- 3. Ambil semua PO Items sekaligus ---
		po_details = frappe.get_all(
			"Purchase Order Materials",
			filters={"name": ["in", [k[1] for k in po_map.keys()]]},
			fields=["name", "qty", "accepted_qty"]
		)

		po_detail_map = {d.name: d for d in po_details}

		# --- 4. Update PO Items ---
		for (po, po_detail), qty_delta in po_map.items():
			if po_detail not in po_detail_map:
				continue

			item = po_detail_map[po_detail]

			total_received = flt(item.accepted_qty) + qty_delta
			total_received = max(total_received, 0)  # prevent negative

			percentage = (
				(total_received / flt(item.qty)) * 100
				if item.qty else 0
			)

			frappe.db.set_value(
				"Purchase Order Materials",
				po_detail,
				{
					"accepted_qty": total_received,
					"percentage_accepted_qty": percentage
				},
				update_modified=False
			)

		# --- 5. Update PO Status ---
		self.update_po_status({k[0] for k in po_map.keys()})

	def update_po_status(self, purchase_orders):

		if not purchase_orders:
			return

		for name in purchase_orders:
			frappe.get_doc("Purchase Order", name).set_status()
			
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