# Copyright (c) 2026, Krisna Jufer and contributors
# For license information, please see license.txt


import frappe

from datetime import (
	date,
	time,
	datetime
)
from frappe.model.document import Document
from frappe.query_builder.functions import ( 
	Sum, 
	Coalesce
)
from pypika import Case

class StockLedgerEntry(Document):
	pass

def make_sle(parent:dict, child:dict):
	last_qty_change = calculate_past_sle(child.material_code, parent.posting_date, parent.posting_time, parent.modified)
	qty = child.qty if parent.doctype in ("Purchase Receipt") else child.qty * -1
	sle = frappe.new_doc("Stock Ledger Entry")
	sle.voucher_type = parent.doctype
	sle.voucher_no = parent.name
	sle.material_code = child.material_code
	sle.material_name = child.material_name
	sle.posting_date = parent.posting_date
	sle.posting_time = parent.posting_time
	sle.qty_change = qty
	sle.qty_after_transaction = last_qty_change + qty
	sle.save()
	update_material_stock(child.material_code)
	filters = {
		"voucher_type" : parent.doctype,
		"voucher_no" : parent.name,
		"material_code": child.material_code
	}
	current_sle = frappe.db.get_value("Stock Ledger Entry", filters, "*")
	repost_future_sle(child.material_code, parent.posting_date, parent.posting_time, current_sle)
	if parent.doctype in ("Purchase Receipt"):
		min_max_update(sle, child)

def calculate_past_sle(material_code:str, posting_date:date, posting_time:time, modified:datetime):

	SLE = frappe.qb.DocType("Stock Ledger Entry")

	date_condition = (
		(SLE.posting_date < posting_date) |
		((SLE.posting_date == posting_date) & (SLE.posting_time <= posting_time))
	)

	result = (
		frappe.qb.from_(SLE)
		.select(Sum(SLE.qty_change).as_("last_qty_change"))
		.where(
			(SLE.material_code == material_code) &
			date_condition &
			(SLE.modified < modified) &
			(SLE.is_cancelled == 0)
		)
		.run(as_dict=True)
	)

	return (result[0].get("last_qty_change") or 0) if result else 0

def get_future_sle(material_code:str, posting_date:date, posting_time:time, creation:datetime):
	SLE = frappe.qb.DocType("Stock Ledger Entry")

	date_condition = (
		(SLE.posting_date > posting_date) |
		((SLE.posting_date == posting_date) & (SLE.posting_time >= posting_time))
	)

	query = (
		frappe.qb.from_(SLE)
		.select(SLE.name, SLE.qty_change)
		.where(SLE.material_code == material_code)
		.where(date_condition)
		.where(SLE.creation > creation)
		.where(SLE.is_cancelled == 0)
	)

	result = query.run(as_dict=True)
	return result

def repost_future_sle(material_code:str, posting_date:date, posting_time:time, current_sle:dict):
	last_qty_change = calculate_past_sle(material_code, posting_date, posting_time, current_sle.creation)
	qty_after_transaction = 0
	data = get_future_sle(material_code, posting_date, posting_time, current_sle.creation)

	for row in data:
		qty_after_transaction += last_qty_change + row.qty_change

		frappe.db.set_value("Stock Ledger Entry", row.name, "qty_after_transaction", qty_after_transaction)

def cancel_sle(parent, child):
	filters = {
		"voucher_type" : parent.doctype,
		"voucher_no" : parent.name,
		"material_code": child.material_code
	}
	
	frappe.db.set_value("Stock Ledger Entry", filters, "is_cancelled", 1)
	current_sle = frappe.db.get_value("Stock Ledger Entry", filters, "*")
	repost_future_sle(child.material_code, parent.posting_date, parent.posting_time, current_sle)
	update_material_stock(child.material_code)


def calculate_material_stock(material_code:str):

	SLE = frappe.qb.DocType("Stock Ledger Entry")

	in_qty_case = Case() \
		.when(SLE.voucher_type == "Purchase Receipt", SLE.qty_change) \
		.else_(0)

	manufacture_out_case = Case() \
		.when(SLE.voucher_type == "Manufacture", SLE.qty_change) \
		.else_(0)

	issue_qty_case = Case() \
		.when(SLE.voucher_type == "Material Issue", SLE.qty_change) \
		.else_(0)

	query = (
		frappe.qb.from_(SLE)
		.select(
			Coalesce(Sum(SLE.qty_change), 0).as_("actual_qty"),
			Coalesce(Sum(in_qty_case), 0).as_("in_qty"),
			Coalesce(Sum(manufacture_out_case), 0).as_("out_qty"),
			Coalesce(Sum(issue_qty_case), 0).as_("issue_qty")
		)
		.where(
			(SLE.material_code == material_code) &
			(SLE.is_cancelled == 0)
		)
	)

	result = query.run(as_dict=True)
	data = result[0] if result else {}

	# --- Normalize jadi positif ---
	data["out_qty"] = abs(data.get("out_qty", 0))
	data["issue_qty"] = abs(data.get("issue_qty", 0))

	return data

def update_material_stock(material_code:str):
	stock = frappe.db.get_value(
		"Material Stock",
		{"material_code": material_code},
		"name"
	)

	if not stock:
		return

	res = calculate_material_stock(material_code)

	frappe.db.set_value(
		"Material Stock",
		stock,
		{
			"actual_qty": res["actual_qty"],
			"in_qty": res["in_qty"],
			"out_qty": res["out_qty"],
			"issue_qty": res["issue_qty"],
		}
	)

def min_max_update(sle:dict, child:dict):
    filters = {
		"parent": child.purchase_order,
		"material_code": sle.material_code
	}
    min_max = frappe.db.get_value("Purchase Order Materials", filters, "*")
    if not min_max:
        return
    
    values = {
		"safety_stock": min_max.safety_stock,
		"min_qty": min_max.min_qty,
		"max_qty": min_max.max_qty,
	}
    
    frappe.db.set_value("Material Stock", {"material_code": sle.material_code}, values)