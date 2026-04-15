// Copyright (c) 2026, Krisna Jufer and contributors
// For license information, please see license.txt

frappe.ui.form.on("Purchase Receipt", {
	posting_date(frm) {
        filterPurchaseOrder(frm);
    },
});

frappe.ui.form.on("Purchase Receipt Material", {
    purchase_order(frm, cdt, cdn){
        if (!frm.doc.posting_date) {
            frappe.msgprint(`Mohon isi <b>Tanggal Penerimaan</b> terlebih dahulu !!`);
            frappe.model.remove_from_locals(cdt, cdn);
            frm.refresh_field("materials"); // ganti "items" dengan nama field child table kamu
            return;
        }
        filterMaterialCode(frm, cdt, cdn);
    },
    
    material_code(frm, cdt, cdn){
        setPurchaseOrderMaterials(frm, cdt, cdn);
    }
})

function filterMaterialCode(frm, cdt, cdn) {
    frm.fields_dict.materials.grid.grid_rows_by_docname[cdn].get_field("material_code").get_query = (doc, cdt, cdn) => {
        const curRow = locals[cdt][cdn];
        let purchase_order = curRow.purchase_order;
        return {
            query: "bouquet_stock.bouquet_stock.doctype.purchase_receipt.purchase_receipt.filter_material_code",
            filters: {
                "purchase_order": purchase_order
            }
        }
    }
}

function filterPurchaseOrder(frm) {
    if (!frm.doc.posting_date) {
        frappe.msgprint(`Mohon isi <b>Tanggal Penerimaan</b> terlebih dahulu !!`);
        return;
    }
    frm.set_query("purchase_order", "materials", () => {
        return {
            filters: {
                docstatus: ["=", 1],
                percentage_accepted_qty: ["<", 99.99],
                posting_date: ["<=", frm.doc.posting_date]
            }
        }
    });
}

function setPurchaseOrderMaterials(frm, cdt, cdn) {
    const curRow = locals[cdt][cdn];
    if (!curRow.purchase_order) {
        frappe.msgprint(`Mohon <b>Kode Pemesanan</b> terlebih dahulu !!`)
        frappe.model.remove_from_locals(cdt, cdn);
        frm.refresh_field("materials");
        return;
    }
    
    let filters = {
        "parent": curRow.purchase_order,
        "material_code": curRow.material_code,
    };

    let values = [
        "name", "qty", "price", "accepted_qty", "current_qty" 
    ]

    frappe.call({
        "method": "bouquet_stock.bouquet_stock.doctype.purchase_order.purchase_order.get_po_detail",
        "args": {
            filters,
            values
        },
        freeze: true,
        callback: (r) => {
            if (r.message) {
                const res = r.message;
                frappe.model.set_value(cdt, cdn, {
                    "po_detail": res.name,
                    "current_qty": res.current_qty,
                    "price": res.price,
                    "accepted_qty": res.accepted_qty,
                    "ordered_qty": res.qty,
                    "qty": res.qty - res.accepted_qty
                });
                frm.refresh_field("materials")
            }
        },
        error: (r) => {
            console.log(r.message);
        }
    })

}