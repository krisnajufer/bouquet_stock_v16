# Copyright (c) 2026, Krisna Jufer and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PurchaseOrder(Document):
	def validate(self):
		self.set_missing_values()
		self.calculate_totals()

	def set_missing_values(self):
		if not self.supplier_name:
			self.supplier_name = frappe.db.get_value("Supplier", self.supplier_code, "supplier_name")

	def calculate_totals(self):
		self.grand_total = 0
		for row in self.materials:
			self.grand_total += row.amount = row.price * row.qty