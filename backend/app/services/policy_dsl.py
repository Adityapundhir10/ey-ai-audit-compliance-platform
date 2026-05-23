from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List
from app.schemas import ExtractedInvoice, ReconciliationResult


@dataclass
class PolicyCheck:
    name: str
    severity: str
    passed: bool
    message: str


class PolicyDSL:
    """Small policy evaluation DSL for auditable finance controls."""

    def evaluate(self, invoice: ExtractedInvoice, reconciliation: ReconciliationResult) -> list[PolicyCheck]:
        checks = [
            self._check_total_positive(invoice),
            self._check_tax_reasonable(invoice),
            self._check_po_match(reconciliation),
            self._check_high_value(invoice),
            self._check_extraction_confidence(invoice),
        ]
        return checks

    def _check_total_positive(self, invoice: ExtractedInvoice) -> PolicyCheck:
        return PolicyCheck("invoice_total_positive", "critical", invoice.total > 0, "Invoice total must be positive")

    def _check_tax_reasonable(self, invoice: ExtractedInvoice) -> PolicyCheck:
        tax_rate = invoice.tax / max(invoice.subtotal, 1.0)
        return PolicyCheck("tax_rate_reasonable", "medium", 0 <= tax_rate <= 0.30, f"Tax rate {tax_rate:.2%} should be within expected range")

    def _check_po_match(self, reconciliation: ReconciliationResult) -> PolicyCheck:
        return PolicyCheck("po_reconciliation", "critical", reconciliation.matched, "; ".join(reconciliation.reasons) or "PO matched")

    def _check_high_value(self, invoice: ExtractedInvoice) -> PolicyCheck:
        return PolicyCheck("high_value_approval", "high", invoice.total <= 500000, "Invoices above INR 500000 require Finance Controller and Procurement Head approval")

    def _check_extraction_confidence(self, invoice: ExtractedInvoice) -> PolicyCheck:
        return PolicyCheck("extraction_confidence", "medium", invoice.confidence >= 0.85, "Extraction confidence must be at least 0.85 for auto-posting")
