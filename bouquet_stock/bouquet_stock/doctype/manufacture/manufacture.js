// Copyright (c) 2026, Krisna Jufer and contributors
// For license information, please see license.txt

frappe.ui.form.on("Manufacture", {
	refresh(frm) {
        filterBouquet(frm);
	},
    bouquet_code(frm){
        getBouquetMaterial(frm);
    },
    posting_date(frm){
        getBouquetMaterial(frm);
    },
    posting_time(frm){
        getBouquetMaterial(frm);
    },
    qty(frm){
        getBouquetMaterial(frm);
    },
});


function filterBouquet(frm) {
    frm.set_query("bouquet_code", () => {
        return {
            filters: {
                "disabled": 0
            }
        }
    });
}

function getBouquetMaterial(frm) {
    let bouquetCode = frm.doc.bouquet_code;
    let postingDate = frm.doc.posting_date;
    let postingTime = frm.doc.posting_time;
    let qty = frm.doc.qty;

    if (!bouquetCode) {
        frappe.msgprint(`Mohon untuk mengisi <b>Kode Bouquet</b> terlebih dahulu !!`);
        return;
    }
    if (!postingDate) {
        frappe.msgprint(`Mohon untuk mengisi <b>Tanggal Pembentukan</b> terlebih dahulu !!`);
        return;
    }
    if (!postingTime) {
        frappe.msgprint(`Mohon untuk mengisi <b>Waktu Pembentukan</b> terlebih dahulu !!`);
        return;
    }
    if (!qty || qty < 1) {
        frappe.msgprint(`Mohon untuk mengisi <b>Qty</b> terlebih dahulu !!`);
        return;
    }

    frappe.call({
        method: "bouquet_stock.bouquet_stock.doctype.manufacture.manufacture.get_bouquet_material_calculation",
        args: {
            "bouquet_code":bouquetCode,
            "posting_date": postingDate,
            "posting_time": postingTime,
            "qty": qty
        },
        freeze: true,
        callback: (r) => {
        // on success
            console.log(r.message);
            const result = r.message;
            if (result) {
                frm.clear_table("materials");
                frm.refresh_field("materials");
                
                result.forEach(row => {
                    frm.add_child("materials", row);
                });
                frm.refresh_field("materials");
            }
        },
        error: (r) => {
        // on error
            console.log(r.message);  
        } 
    })
}