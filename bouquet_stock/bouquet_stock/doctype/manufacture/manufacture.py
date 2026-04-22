# Copyright (c) 2026, Krisna Jufer and contributors
# For license information, please see license.txt

import frappe

from frappe.model.document import Document
from datetime import (
	date,
	time
)

from bouquet_stock.utils import (
	calculate_sle_by_period
)
from bouquet_stock.bouquet_stock.doctype.stock_ledger_entry.stock_ledger_entry import (
	make_sle,
	cancel_sle
)

class Manufacture(Document):
	
	def validate(self):
		self.validate_qty()

	def validate_qty(self):
		materials = []
		for row in self.materials:
			if row.qty > row.current_qty:
				materials.append(row.material_code)
		if not materials:
			return
		material_msg = ", ".join(materials)
		frappe.throw(f"Material (<b>{material_msg}</b>) tidak mencukupi")

	def on_submit(self):
		self.process_stock_ledger_entries()
		
	def on_cancel(self):
		self.process_stock_ledger_entries(True)

	def process_stock_ledger_entries(self, cancelled=False):
		for child in self.materials:
			if cancelled:
				cancel_sle(self, child)
			else:
				make_sle(self, child)


@frappe.whitelist()
def get_bouquet_material_calculation(bouquet_code: str, qty: float, posting_date: date, posting_time: time):
    bouquet_materials = frappe.db.get_all(
        "Bouquet Material",
        filters={"parent": bouquet_code},
        fields=["material_code", "material_name", "required_qty"]
    )

    bm_map = {}
    material_codes = []

    for row in bouquet_materials:
        bm_map[row.material_code] = frappe._dict({
            "material_code": row.material_code,
            "material_name": row.material_name,
            "qty": row.required_qty * qty,
            "current_qty": 0
        })
        material_codes.append(row.material_code)

    sle_materials = calculate_sle_by_period(material_codes, posting_date, posting_time)

    for sle in sle_materials:
        if sle.material_code in bm_map:
            bm_map[sle.material_code]["current_qty"] = sle.last_qty_change

    for key, val in bm_map.items():
        status = "Mencukupi"
        if val.get("current_qty") < val.get("qty"):
            status = "Tidak Mencukupi"

        val["status"] = status

    return list(bm_map.values())