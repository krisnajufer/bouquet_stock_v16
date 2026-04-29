# Copyright (c) 2026, Krisna Jufer and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from pypika import Case, Order

from frappe.query_builder.functions import Concat

def execute(filters: dict | None = None):
	"""Return columns and data for the report.

	This is the main entry point for the report. It accepts the filters as a
	dictionary and should return columns and data. It is called by the framework
	every time the report is refreshed or a filter is updated.
	"""
	columns = get_columns()
	data = get_data(filters)

	return columns, data


def get_columns() -> list[dict]:
	"""Return columns for the report.

	One field definition per column, just like a DocType field definition.
	"""
	return [
		{
			"label": _("Kode Material"),
			"fieldname": "material_code",
			"fieldtype": "Link",
			"options": "Material"
		},
		{
			"label": _("Nama Material"),
			"fieldname": "material_name",
			"fieldtype": "Data",
		},
		{
			"label": _("Qty Masuk"),
			"fieldname": "in_qty",
			"fieldtype": "Int",
			"default": 0
		},
		{
			"label": _("Qty Keluar"),
			"fieldname": "out_qty",
			"fieldtype": "Int",
			"default": 0
		},
		{
			"label": _("Qty Issue"),
			"fieldname": "issue_qty",
			"fieldtype": "Int",
			"default": 0
		},
		{
			"label": _("Qty Balance"),
			"fieldname": "balance_qty",
			"fieldtype": "Int",
			"default": 0
		},
		{
			"label": _("Posting Date Time"),
			"fieldname": "posting_date_time",
			"fieldtype": "Datetime",
		},
		{
			"label":_("Tipe Transaksi"),
			"fieldname": "voucher_type",
			"fieldtype": "Link",
			"options": "DocType",
		},
		{
			"label":_("No Transaksi"),
			"fieldname": "voucher_no",
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
		},

	]


def get_data(filters: dict) -> list[list]:
	"""Return data for the report.

	The report data is a list of rows, with each row being a list of cell values.
	"""
	
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
		frappe.qb.select(
			SLE.material_code,
			SLE.material_name,
			in_qty_case.as_("in_qty"),
			manufacture_out_case.as_("out_qty"),
			issue_qty_case.as_("issue_qty"),
			SLE.qty_after_transaction.as_("balance_qty"),
			Concat(SLE.posting_date, " ",SLE.posting_time).as_("posting_date_time"),
			SLE.voucher_type,
			SLE.voucher_no
		)
		.from_(SLE)
	)

	if material_code := filters.get("material_code"):
		query = (
			query.where(
				SLE.material_code == material_code
			)
		)
	
	if voucher_type := filters.get("voucher_type"):
		query = (
			query.where(
				SLE.voucher_type == voucher_type
			)
		)
	
	if filters.get("from_date") and filters.get("to_date"):
		query = (
			query.where(
				SLE.posting_date.between(filters.get("from_date"), filters.get("to_date"))
			)
		)

	query = (
		query.where(SLE.is_cancelled == 0)
		.orderby(SLE.posting_date, Order.asc)
		.orderby(SLE.posting_time, Order.asc)
		.orderby(SLE.creation, Order.asc)
	)
	return query.run(as_dict=True)