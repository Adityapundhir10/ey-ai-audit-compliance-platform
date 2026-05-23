import pytest
from app.services.document_intelligence import InvoiceExtractor

RAW = """
Invoice Number: INV-TEST-1
Vendor ID: V-ACME
Vendor Name: Acme Facilities Pvt Ltd
PO Number: PO-9001
Invoice Date: 2025-06-15
Due Date: 2025-07-15
Currency: INR
Subtotal: 10000
Tax: 1800
Total: 11800
ITEM|Facility audit service|qty=1|unit=10000|amount=10000|gl=GL-600|cc=CC-AUDIT
"""


@pytest.mark.asyncio
async def test_invoice_extraction():
    invoice = await InvoiceExtractor().extract(RAW)
    assert invoice.invoice_id == "INV-TEST-1"
    assert invoice.vendor_id == "V-ACME"
    assert invoice.total == 11800
    assert invoice.confidence > 0.7
