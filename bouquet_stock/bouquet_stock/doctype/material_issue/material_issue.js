// Copyright (c) 2026, Krisna Jufer and contributors
// For license information, please see license.txt

frappe.ui.form.on("Material Issue", {
	refresh(frm) {

	},
    material_code(frm){
        getActualQty(frm);
    },
    posting_date(frm){
        getActualQty(frm);
    },
    posting_time(frm){
        getActualQty(frm);
    }
});


function getActualQty(frm) {
    if (!frm.doc.material_code || !frm.doc.posting_date || !frm.doc.posting_time) {
        return
    }
    frappe.call({
        method: "bouquet_stock.bouquet_stock.doctype.material_issue.material_issue.get_last_qty_change",
        args: {
            material_code: frm.doc.material_code,
            posting_date: frm.doc.posting_date,
            posting_time: frm.doc.posting_time,
        },
        freeze: true,
        callback: (r) => {
            res = r.message;
            frm.set_value("actual_qty", res)
            frm.refresh_field("actual_qty");
        },
        error: (r) => {
            console.log(r);
        }
    })
}