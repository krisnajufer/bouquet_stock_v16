import frappe

def get_actual_qty(material_code : str):
    return frappe.db.get_value("Material Stock", {"material_code": material_code}, "actual_qty")

def get_min_max_calculation(max_qty : float, avg_qty : float, lead_time : float):
    safety_stock = max((max_qty - avg_qty) * lead_time, 0) or 0
    min_qty = avg_qty * lead_time + safety_stock or 0
    max_qty_stock = min_qty * 2 or 0

    return frappe._dict({
        "safety_stock": safety_stock,
        "min_qty": min_qty,
        "max_qty": max_qty_stock,
    })