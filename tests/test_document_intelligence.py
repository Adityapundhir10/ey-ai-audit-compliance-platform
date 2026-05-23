from ey_audit_ai.document_intelligence import SchemaConstrainedInvoiceExtractor


def test_extract_invoice_from_text():
    text = """
    INVOICE
    Invoice ID: INV-1
    Vendor ID: VND-1
    Vendor Name: Demo Vendor
    Invoice Date: 2025-07-01
    Due Date: 2025-07-31
    PO ID: PO-1
    Currency: INR
    Payment Terms: Net 30
    Line Items
    Service | 2 | 100.00 | 200.00 | GL-1
    Subtotal: 200.00
    Tax: 36.00
    Total: 236.00
    """
    invoice = SchemaConstrainedInvoiceExtractor().extract(text)
    assert invoice.invoice_id == "INV-1"
    assert invoice.total == 236.0
    assert len(invoice.line_items) == 1
