// Copyright (c) 2026, Krisna Jufer and contributors
// For license information, please see license.txt

frappe.query_reports["Stock Movement"] = {
	filters: [
		{
			"fieldname": "material_code",
			"label": __("Kode material"),
			"fieldtype": "Link",
			"options": "Material",
		},
		{
			"fieldname": "from_date",
			"label": __("Dari Tanggal"),
			"fieldtype": "Date"
		},
		{
			"fieldname": "to_date",
			"label": __("Sampai Tanggal"),
			"fieldtype": "Date"
		},
		{
			"fieldname": "voucher_type",
			"label": __("Tipe Transaksi"),
			"fieldtype": "Select",
			"options": "Purchase Receipt\nManufacture\nMaterial Issue"
		}
	],
    formatter: function (value, row, column, data, default_formatter) {
        // Call default formatter first
        value = default_formatter(value, row, column, data);

        // Conditional styling based on value
        if (column.fieldname == "in_qty") {
            value = `<span style="color:green; font-weight:bold;">${value}</span>`;
        }
        if (column.fieldname == "out_qty") {
            value = `<span style="color:red; font-weight:bold;">${value}</span>`;
        }
        if (column.fieldname == "issue_qty") {
            value = `<span style="color:orange; font-weight:bold;">${value}</span>`;
        }
        return value;
	}
};
