import re
from pathlib import Path
from typing import Any, Dict, Optional
from app.core.config import get_settings
from app.schemas import ExtractedInvoice, LineItem


class OCRNormalizer:
    """Cleans noisy OCR output from invoices and procurement documents."""

    OCR_REPLACEMENTS = {
        "lNV": "INV",
        "O0": "00",
        "₹": "INR ",
        "Rs.": "INR ",
        "Amount Due": "Total",
        "P0": "PO",
    }

    def normalize(self, raw_text: str) -> str:
        text = raw_text.replace("\r", "\n")
        for src, dst in self.OCR_REPLACEMENTS.items():
            text = text.replace(src, dst)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


class AzureFormRecognizerAdapter:
    """Optional Azure Document Intelligence adapter.

    This adapter intentionally falls back to local parsing unless endpoint/key are
    configured. That makes the repository runnable without cloud credentials.
    """

    def __init__(self):
        self.settings = get_settings()

    def enabled(self) -> bool:
        return bool(self.settings.azure_form_recognizer_endpoint and self.settings.azure_form_recognizer_key)

    async def analyze_invoice(self, file_path: Optional[str], raw_text: str) -> Dict[str, Any]:
        if not self.enabled():
            return {"enabled": False, "provider": "local_fallback", "fields": {}}
        # Production placeholder:
        # from azure.ai.formrecognizer.aio import DocumentAnalysisClient
        # from azure.core.credentials import AzureKeyCredential
        # client = DocumentAnalysisClient(...)
        # poller = await client.begin_analyze_document(...)
        # result = await poller.result()
        # return parsed result
        return {"enabled": True, "provider": "azure_form_recognizer", "fields": {}}


class InvoiceExtractor:
    def __init__(self):
        self.normalizer = OCRNormalizer()
        self.azure = AzureFormRecognizerAdapter()

    async def extract(self, raw_text: str, source_document: Optional[str] = None) -> ExtractedInvoice:
        normalized = self.normalizer.normalize(raw_text)
        await self.azure.analyze_invoice(source_document, normalized)
        parsed = self._regex_extract(normalized)
        parsed["source_document"] = source_document
        return ExtractedInvoice(**parsed)

    def _regex_extract(self, text: str) -> Dict[str, Any]:
        def find(pattern: str, default: str = "") -> str:
            m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            return m.group(1).strip() if m else default

        invoice_id = find(r"Invoice\s*(?:ID|No|Number)\s*[:#-]\s*([A-Z0-9-]+)", "INV-UNKNOWN")
        vendor_id = find(r"Vendor\s*ID\s*[:#-]\s*([A-Z0-9-]+)", "V-UNKNOWN")
        vendor_name = find(r"Vendor\s*Name\s*[:#-]\s*(.+)", "Unknown Vendor")
        po_number = find(r"PO\s*(?:Number|No)\s*[:#-]\s*([A-Z0-9-]+)", "PO-UNKNOWN")
        invoice_date = find(r"Invoice\s*Date\s*[:#-]\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", "2025-06-01")
        due_date = find(r"Due\s*Date\s*[:#-]\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", "2025-07-01")
        currency = find(r"Currency\s*[:#-]\s*([A-Z]{3})", "INR")

        def money(label: str, default: float = 0.0) -> float:
            value = find(rf"{label}\s*[:#-]\s*(?:INR|USD|EUR)?\s*([0-9,]+(?:\.[0-9]+)?)", str(default))
            try:
                return float(value.replace(",", ""))
            except Exception:
                return default

        subtotal = money("Subtotal")
        tax = money("Tax")
        total = money("Total") or subtotal + tax

        line_items = []
        for match in re.finditer(r"ITEM\|([^|]+)\|qty=([0-9.]+)\|unit=([0-9.]+)\|amount=([0-9.]+)\|gl=([A-Z0-9-]+)\|cc=([A-Z0-9-]+)", text):
            line_items.append(
                LineItem(
                    description=match.group(1).strip(),
                    quantity=float(match.group(2)),
                    unit_price=float(match.group(3)),
                    amount=float(match.group(4)),
                    gl_code=match.group(5),
                    cost_center=match.group(6),
                )
            )
        if not line_items and subtotal > 0:
            line_items.append(LineItem(description="Extracted invoice total", quantity=1, unit_price=subtotal, amount=subtotal))

        fields_found = sum(1 for x in [invoice_id, vendor_id, vendor_name, po_number, subtotal, tax, total] if x not in ["", 0.0, "INV-UNKNOWN", "V-UNKNOWN", "Unknown Vendor", "PO-UNKNOWN"])
        confidence = min(0.97, 0.55 + fields_found * 0.06 + min(len(line_items), 3) * 0.04)

        return {
            "invoice_id": invoice_id,
            "vendor_id": vendor_id,
            "vendor_name": vendor_name,
            "po_number": po_number,
            "invoice_date": invoice_date,
            "due_date": due_date,
            "currency": currency,
            "subtotal": subtotal,
            "tax": tax,
            "total": total,
            "line_items": line_items,
            "confidence": round(confidence, 3),
        }


def read_document_text(path: str) -> str:
    p = Path(path)
    return p.read_text(encoding="utf-8")
