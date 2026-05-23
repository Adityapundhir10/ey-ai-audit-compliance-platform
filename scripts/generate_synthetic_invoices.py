import json
import random
from pathlib import Path

vendors = ["V-FAC-001", "V-IT-002", "V-LOG-003", "V-MKT-004"]
pos = ["PO-2025-001", "PO-2025-002", "PO-2025-003", "PO-2025-004"]

rows = []
for i in range(100):
    subtotal = random.randint(25000, 800000)
    tax = round(subtotal * 0.18, 2)
    rows.append({
        "invoice_id": f"INV-SYN-{i+1:04d}",
        "vendor_id": random.choice(vendors),
        "po_number": random.choice(pos),
        "subtotal": subtotal,
        "tax": tax,
        "total": subtotal + tax,
    })
Path("data/generated_invoices.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
print("Generated data/generated_invoices.json")
