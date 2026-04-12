# Copyright (c) 2026, Krisna Jufer and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Material(Document):
	def after_insert(self):
		self.make_material_stock()

	def on_trash(self):
		self.delete_material_stock()

	def make_material_stock(self):
		values = {
			"doctype": "Material Stock",
			"material_code": self.name, 
			"material_name": self.material_name, 
		}

		frappe.get_doc(values).insert(ignore_permissions=True)

	def delete_material_stock(self):
		frappe.get_doc("Material Stock", {"material_code": self.material_code})