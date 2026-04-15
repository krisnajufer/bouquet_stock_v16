# Copyright (c) 2026, Krisna Jufer and contributors
# For license information, please see license.txt
import json
from datetime import (
	date,
	timedelta
)

import frappe

from frappe.model.document import Document
from frappe.query_builder.functions import (
	Max, 
	Sum, 
	Abs,
	Coalesce
)

from bouquet_stock.utils import (
	get_min_max_calculation,
	get_actual_qty
)

class PurchaseOrder(Document):
	def before_validate(self):
		self.set_missing_values()
		self.set_min_max_values()
		self.calculate_totals()

	def on_submit(self):
		self.set_status()

	def set_missing_values(self):
		if not self.supplier_name:
			self.supplier_name = frappe.db.get_value("Supplier", self.supplier_code, "supplier_name")

	def calculate_totals(self):
		total = 0
		for row in self.materials:
			row.amount = row.price * row.qty
			total += row.amount
		self.grand_total = total

	def set_min_max_values(self):
		for row in self.materials:
			res = min_max_calculation(row.material_code, self.posting_date)
			row.current_qty = res.current_qty
			row.safety_stock = res.safety_stock
			row.lead_time = res.lead_time
			row.min_qty = res.min
			row.max_qty = res.max
			row.qty = (res.max - res.current_qty) if res.max and res.max > 0 else row.qty

	def set_status(self):
		if self.percentage_accepted_qty > 0 and self.percentage_accepted_qty >= 99.99:
			self.status = "Diterima Semua"
		elif self.percentage_accepted_qty > 0 and self.percentage_accepted_qty < 99.99:
			self.status = "Diterima Sebagian"
		else:
			self.status = "Belum Diterima"

@frappe.whitelist()
def min_max_calculation(material_code:str, posting_date:date):
	lead_time = frappe.db.get_single_value("Stock Settings", "lead_time")
	calculation_transaction = frappe.db.get_single_value("Stock Settings", "calculation_transaction")
	start_date = posting_date - timedelta(days=calculation_transaction)
	SLE = frappe.qb.DocType("Stock Ledger Entry")

	query = (
		frappe.qb.select(
			Coalesce(Max(Abs(SLE.qty_change)), 0).as_("max_qty"),
			Coalesce((Sum(Abs(SLE.qty_change)) / calculation_transaction), 0).as_("avg_qty")
		)
		.from_(SLE)
		.where(
			(SLE.voucher_type == "Manufacture") &
			(SLE.material_code == material_code) &
			(SLE.is_cancelled == 0) &
			(SLE.posting_date.between(start_date, posting_date))
		)
	)

	result = query.run(as_dict=True)[0]
	actual_qty = get_actual_qty(material_code)
	calculation_method = get_min_max_calculation(result.max_qty, result.avg_qty, lead_time)
	return frappe._dict({
		"safety_stock": calculation_method.safety_stock,
		"min": calculation_method.min_qty,
		"max": calculation_method.max_qty,
		"current_qty": actual_qty,
		"lead_time": lead_time
	})

@frappe.whitelist()
def get_po_detail(filters: str, values: str):
	# --- Guard clause ---
	filters = json.loads(filters)
	values = json.loads(values)
	
	if not values:
		return {}

	# --- Handle special field ---
	is_actual_qty = "current_qty" in values
	values = [v for v in values if v != "current_qty"]

	# --- Fetch data ---
	po_detail = frappe.db.get_value(
		"Purchase Order Materials",
		filters,
		values,
		as_dict=True
	) or {}

	result = frappe._dict(po_detail)

	# --- Resolve material_code ---
	material_code = (
		filters.get("material_code")
		or po_detail.get("material_code")
	)

	# --- Enrich data ---
	if is_actual_qty and material_code:
		result["current_qty"] = get_actual_qty(material_code)

	return result