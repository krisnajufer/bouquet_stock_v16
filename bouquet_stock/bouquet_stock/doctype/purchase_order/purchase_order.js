// Copyright (c) 2026, Krisna Jufer and contributors
// For license information, please see license.txt

frappe.ui.form.on("Purchase Order", {
	refresh(frm) {
        filterMaterials(frm);
	},

    posting_date(frm){
        recalculateMinMax(frm);
    }
});

frappe.ui.form.on("Purchase Order Materials", {
    materials_remove(frm){
        calculateGrandTotal(frm)
    },
    material_code(frm, cdt, cdn){
        minmaxCalculation(frm, cdt, cdn);
    },
    price(frm, cdt, cdn){
        calculateTotals(frm, cdt, cdn);
    },

    qty(frm, cdt, cdn){
        calculateTotals(frm, cdt, cdn);
    }
})


function calculateTotals(frm, cdt, cdn) {
    calculateAmount(frm, cdt, cdn);
    calculateGrandTotal(frm);
}

function calculateAmount(frm, cdt, cdn) {
    const curRow = locals[cdt][cdn];
    
    let amount = 0;
    if (curRow.price > 0 && curRow.qty > 0) {
        amount = curRow.price * curRow.qty;        
    }

    frappe.model.set_value(cdt, cdn, "amount", amount);
    frm.refresh_field("materials");
}

function calculateGrandTotal(frm) {
    const materials = frm.doc.materials;
    let total = 0;
    materials.forEach(row => {
        total += row.amount;
    });
    frm.set_value("grand_total", total);
    frm.refresh_field("grand_total");
}

function minmaxCalculation(frm, cdt, cdn) {
    const curRow = locals[cdt][cdn]
    if (!frm.doc.posting_date) {
        frappe.msgprint(`<b>Tanggal Pemesanan</b> wajib diisi terlebih dahulu sebelum menambahkan Material`);
        frappe.model.clear_doc(cdt, cdn);
        frm.refresh_field("materials");
        return
    }
    if (!curRow.material_code) {
        return
    }

    frappe.call({
        method: "bouquet_stock.bouquet_stock.doctype.purchase_order.purchase_order.min_max_calculation",
        args: {
            material_code: curRow.material_code,
            posting_date: frm.doc.posting_date,
        },
        freeze: true,
        callback: (r) => {
            if (r.message) {
                res = r.message;
                let ordered_qty = curRow.qty ? curRow.qty : 0;
                values = {
                    "safety_stock": res.safety_stock,
                    "current_qty": res.current_qty,
                    "min_qty": res.min,
                    "max_qty": res.max,
                    "lead_time": res.lead_time,
                    "qty": res.max >  0 ? res.max - ordered_qty: ordered_qty 
                };
                frappe.model.set_value(cdt, cdn, values);
                frm.refresh_field("materials");
            }
        },
        error: (r) => {
            console.log(r);
            
        }
    })
}

function recalculateMinMax(frm) {
    const materials = frm.doc.materials;
    
    materials.forEach(row => {
        minmaxCalculation(frm, row.doctype, row.name);
    });
}

function filterMaterials(frm) {
    frm.set_query("material_code", "materials", (doc) => {
        return {
            query:"bouquet_stock.bouquet_stock.doctype.purchase_order.purchase_order.filter_materials"
        }
    })
}