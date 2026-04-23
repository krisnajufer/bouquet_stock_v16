(function () {

    // ⛔ cegah duplikasi load
    if (window.__stock_alert_loaded) return;
    window.__stock_alert_loaded = true;

    let dialog_shown = false;

    function check_stock() {
        if (dialog_shown) return;

        frappe.call({
            method: "bouquet_stock.bouquet_stock.doctype.material_stock.material_stock.get_critical_stock",
            callback(r) {
                if (r.message && r.message.result.length && r.message.is_critical_stock_alert) {
                    show_dialog(r.message.result);
                }
            }
        });
    }

    function show_dialog(data) {
        dialog_shown = true;

        let rows = data.map(d => `
            <tr>
                <td>${d.material_code}</td>
                <td>${d.material_name}</td>
                <td>${d.actual_qty}</td>
                <td>${d.safety_stock}</td>
                <td>${d.min_qty}</td>
                <td>${d.max_qty}</td>
                <td>
                    <button 
                        class="btn btn-sm btn-primary order-item"
                        data-item="${d.material_code}"
                        data-name="${d.material_name}"
                        data-qty="${(d.max_qty - d.actual_qty) || 1}">
                        Pesan
                    </button>
                </td>
            </tr>
        `).join('');

        const dialog = new frappe.ui.Dialog({
            title: __('Peringatan Stok Kritis'),
            static: true,
            fields: [
                {
                    fieldtype: 'HTML',
                    options: `
                        <p style="color:red; font-weight:bold">
                            Terdapat material dengan stok di bawah batas minimum.
                            Silakan lakukan pemesanan segera.
                        </p>
                        <table class="table table-bordered">
                            <thead>
                                <tr>
                                    <th>Material</th>
                                    <th>Nama Material</th>
                                    <th>Stok Aktual</th>
                                    <th>Safety Stock</th>
                                    <th>Min</th>
                                    <th>Max</th>
                                    <th>Aksi</th>
                                </tr>
                            </thead>
                            <tbody>${rows}</tbody>
                        </table>
                    `
                }
            ],
            size: 'extra-large',
        });

        dialog.show();

        // ⛔ hilangkan tombol close (X)
        dialog.$wrapper.find('.modal-header .close').remove();
        dialog.$wrapper.on('click', '.order-item', function () {
            const material_code = $(this).data('item');
            const material_name = $(this).data('name');

            let qty = parseFloat($(this).data('qty'));
            if (isNaN(qty) || qty <= 0) qty = 1;

            frappe.new_doc('Purchase Order', {}, (doc) => {
                // 🔥 pastikan child table diisi via model
                doc.materials = []
                let row = frappe.model.add_child(doc, "Purchase Order Item", "materials");

                frappe.model.set_value(row.doctype, row.name, "material_code", material_code);
                frappe.model.set_value(row.doctype, row.name, "material_name", material_name);
                frappe.model.set_value(row.doctype, row.name, "qty", qty);

                // optional (kalau ada field mandatory)
                // frappe.model.set_value(row.doctype, row.name, "uom", "Unit");

            });

            dialog.hide();
        });
    }

    // ✅ JALAN SAAT PAGE LOAD / RELOAD
    frappe.after_ajax(() => {
        console.log('OKE SUKSES - AFTER AJAX');
        check_stock();
    });

})();