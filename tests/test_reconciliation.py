from ey_audit_ai.reconciliation import POReconciler
from ey_audit_ai.schemas import Invoice, InvoiceLine, PurchaseOrder


def test_reconciliation_flags_amount_variance():
    invoice = Invoice(
        invoice_id="INV-1",
        vendor_id="VND-1",
        vendor_name="Vendor",
        invoice_date="2025-07-01",
        due_date="2025-07-30",
        po_id="PO-1",
        currency="INR",
        subtotal=1000,
        tax=180,
        total=1180,
        payment_terms="Net 30",
        line_items=[InvoiceLine("Service", 1, 1000, 1000)],
    )
    po = PurchaseOrder(
        po_id="PO-1",
        vendor_id="VND-1",
        currency="INR",
        approved_total=1000,
        remaining_balance=1000,
        valid_from="2025-01-01",
        valid_to="2025-12-31",
        cost_center="CC-1",
        approver_email="a@example.com",
        status="approved",
        line_items=[InvoiceLine("Service", 1, 1000, 1000)],
    )
    result = POReconciler(amount_tolerance_percent=2).reconcile(invoice, po)
    assert not result.matched
    assert any(f.code == "AMOUNT_VARIANCE" for f in result.findings)
    assert any(f.code == "INSUFFICIENT_PO_BALANCE" for f in result.findings)
