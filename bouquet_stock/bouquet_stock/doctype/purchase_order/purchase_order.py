# Copyright (c) 2026, Krisna Jufer and contributors
# For license information, please see license.txt

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
	def validate(self):
		self.set_missing_values()
		self.calculate_totals()

	def set_missing_values(self):
		if not self.supplier_name:
			self.supplier_name = frappe.db.get_value("Supplier", self.supplier_code, "supplier_name")

	def calculate_totals(self):
		total = 0
		for row in self.materials:
			row.amount = row.price * row.qty
			total += row.amount
		self.grand_total = total

@frappe.whitelist()
def min_max_calculation(material_code:str, posting_date:date):
	lead_time = frappe.db.get_single_value("Stock Settings", "lead_time")
	calculation_transaction = frappe.db.get_single_value("Stock Settings", "calculation_transaction")
	start_date = posting_date - timedelta(days=30)
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