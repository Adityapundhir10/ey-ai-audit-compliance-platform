from ey_audit_ai.fraud import ComplianceAnomalyEngine
from ey_audit_ai.schemas import Invoice, VendorProfile


def test_fraud_duplicate_signal():
    invoice = Invoice(
        invoice_id="INV-2",
        vendor_id="VND-1",
        vendor_name="Vendor",
        invoice_date="2025-07-01",
        due_date="2025-07-31",
        po_id="PO-1",
        currency="INR",
        subtotal=1000,
        tax=180,
        total=1180,
        payment_terms="Net 30",
    )
    vendor = VendorProfile("VND-1", "Vendor", "medium", "IN", 900)
    history = [{"invoice_id": "INV-OLD", "vendor_id": "VND-1", "po_id": "PO-1", "invoice_date": "2025-06-29", "total": 1180}]
    score, signals = ComplianceAnomalyEngine().evaluate(invoice, vendor, history)
    assert score > 0.5
    assert any(s.name == "duplicate_invoice_risk" for s in signals)
