# Copyright (c) 2026, Krisna Jufer and contributors
# For license information, please see license.txt

import frappe
from datetime import (
	date,
	time
)

from frappe.model.document import Document
from bouquet_stock.utils import calculate_sle_by_period
from bouquet_stock.bouquet_stock.doctype.stock_ledger_entry.stock_ledger_entry import (
	make_sle,
	cancel_sle
)

class MaterialIssue(Document):
	def validate(self):
		if self.actual_qty < self.qty:
			frappe.throw(f"Actual Qty kurang dari Qty yang akan di issue")

	def on_submit(self):
		self.process_stock_ledger_entries()
		
	def on_cancel(self):
		self.process_stock_ledger_entries(True)

	def on_trash(self):
		frappe.db.delete("Stock Ledger Entry", {"voucher_type": "Manufacture", "voucher_no": self.name})

	def process_stock_ledger_entries(self, cancelled=False):
		if cancelled:
			cancel_sle(self, self)
		else:
			make_sle(self, self)

@frappe.whitelist()
def get_last_qty_change(material_code:str, posting_date:date, posting_time:time):
	list_material_code = [material_code]
	result = calculate_sle_by_period(list_material_code, posting_date, posting_time)

	return result[0].last_qty_change if result and result[0] else 0