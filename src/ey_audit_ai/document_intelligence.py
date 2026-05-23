from __future__ import annotations

import json
import re
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Any

from .schemas import Invoice, InvoiceLine


class OCRNormalizer:
    """Normalizes noisy OCR text from invoices before structured extraction."""

    COMMON_REPLACEMENTS = {
        "lNVOICE": "INVOICE",
        "INV0ICE": "INVOICE",
        "P0": "PO",
        "T0TAL": "TOTAL",
        "₹": "INR ",
        "$": "USD ",
        "\u00a0": " ",
    }

    def normalize(self, text: str) -> str:
        for old, new in self.COMMON_REPLACEMENTS.items():
            text = text.replace(old, new)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"(?i)invoice\s*#", "Invoice ID:", text)
        text = re.sub(r"(?i)po\s*#", "PO ID:", text)
        return text.strip()


class AzureFormRecognizerAdapter:
    """Adapter boundary for Azure Form Recognizer / Document Intelligence.

    In local demo mode, this class uses regex extraction. In enterprise mode, call the
    Azure SDK here and map the response into the same normalized schema.
    """

    def __init__(self, enabled: bool = False):
        self.enabled = enabled

    def analyze_invoice(self, text: str) -> dict[str, Any]:
        if self.enabled:
            raise NotImplementedError(
                "Wire the azure-ai-formrecognizer client here when cloud credentials are available."
            )
        return RegexInvoiceExtractor().extract(text)


class RegexInvoiceExtractor:
    FIELD_PATTERNS = {
        "invoice_id": r"Invoice ID:\s*([A-Z0-9\-]+)",
        "vendor_id": r"Vendor ID:\s*([A-Z0-9\-]+)",
        "vendor_name": r"Vendor Name:\s*(.+)",
        "invoice_date": r"Invoice Date:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})",
        "due_date": r"Due Date:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})",
        "po_id": r"PO ID:\s*([A-Z0-9\-]+)",
        "currency": r"Currency:\s*([A-Z]{3})",
        "subtotal": r"^\s*Subtotal:\s*([0-9,.]+)",
        "tax": r"^\s*Tax:\s*([0-9,.]+)",
        "total": r"^\s*Total:\s*([0-9,.]+)",
        "payment_terms": r"Payment Terms:\s*(.+)",
    }

    def extract(self, text: str) -> dict[str, Any]:
        fields: dict[str, Any] = {}
        confidence_hits = 0
        for key, pattern in self.FIELD_PATTERNS.items():
            match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip()
                if key in {"subtotal", "tax", "total"}:
                    value = float(value.replace(",", ""))
                fields[key] = value
                confidence_hits += 1
        fields["line_items"] = self._extract_line_items(text)
        fields["extracted_confidence"] = round(confidence_hits / len(self.FIELD_PATTERNS), 3)
        return fields

    def _extract_line_items(self, text: str) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        in_section = False
        for raw in text.splitlines():
            line = raw.strip()
            if re.match(r"(?i)^line items", line):
                in_section = True
                continue
            if in_section and (not line or re.match(r"(?i)^(subtotal|tax|total)", line)):
                break
            if in_section:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 4:
                    try:
                        items.append(
                            {
                                "description": parts[0],
                                "quantity": float(parts[1]),
                                "unit_price": float(parts[2].replace(",", "")),
                                "amount": float(parts[3].replace(",", "")),
                                "gl_code": parts[4] if len(parts) > 4 else None,
                            }
                        )
                    except ValueError:
                        continue
        return items


class SchemaConstrainedInvoiceExtractor:
    """Combines OCR cleanup, deterministic extraction, and strict validation."""

    REQUIRED_FIELDS = {
        "invoice_id",
        "vendor_id",
        "vendor_name",
        "invoice_date",
        "due_date",
        "po_id",
        "currency",
        "subtotal",
        "tax",
        "total",
        "payment_terms",
    }

    def __init__(self, recognizer: AzureFormRecognizerAdapter | None = None):
        self.normalizer = OCRNormalizer()
        self.recognizer = recognizer or AzureFormRecognizerAdapter(enabled=False)

    def extract(self, document_text: str, source_document: str | None = None) -> Invoice:
        normalized = self.normalizer.normalize(document_text)
        raw = self.recognizer.analyze_invoice(normalized)
        errors = self.validate_payload(raw)
        if errors:
            raise ValueError("Invoice schema validation failed: " + "; ".join(errors))
        line_items = [InvoiceLine(**item) for item in raw.get("line_items", [])]
        return Invoice(
            invoice_id=raw["invoice_id"],
            vendor_id=raw["vendor_id"],
            vendor_name=raw["vendor_name"],
            invoice_date=raw["invoice_date"],
            due_date=raw["due_date"],
            po_id=raw["po_id"],
            currency=raw["currency"],
            subtotal=float(raw["subtotal"]),
            tax=float(raw["tax"]),
            total=float(raw["total"]),
            payment_terms=raw["payment_terms"],
            line_items=line_items,
            source_document=source_document,
            extracted_confidence=float(raw.get("extracted_confidence", 0.0)),
        )

    def validate_payload(self, payload: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        missing = sorted(self.REQUIRED_FIELDS - set(payload.keys()))
        if missing:
            errors.append(f"missing fields: {missing}")
        if "total" in payload and "subtotal" in payload and "tax" in payload:
            expected_total = round(float(payload["subtotal"]) + float(payload["tax"]), 2)
            observed_total = round(float(payload["total"]), 2)
            if abs(expected_total - observed_total) > 0.05:
                errors.append(f"total mismatch expected {expected_total} observed {observed_total}")
        for date_key in ("invoice_date", "due_date"):
            if date_key in payload:
                try:
                    datetime.strptime(payload[date_key], "%Y-%m-%d")
                except ValueError:
                    errors.append(f"{date_key} must be YYYY-MM-DD")
        if payload.get("currency") not in {"INR", "USD", "EUR", "GBP"}:
            errors.append("unsupported currency")
        return errors


def invoice_to_json(invoice: Invoice) -> str:
    return json.dumps(asdict(invoice), indent=2)
