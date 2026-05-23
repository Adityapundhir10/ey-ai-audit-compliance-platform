from __future__ import annotations

from datetime import datetime
from typing import Iterable

from .schemas import Invoice, PurchaseOrder, ReconciliationFinding, ReconciliationResult, RiskLevel


class POReconciler:
    """Deterministic controls for invoice-to-PO reconciliation."""

    def __init__(self, amount_tolerance_percent: float = 2.0):
        self.amount_tolerance_percent = amount_tolerance_percent

    def reconcile(self, invoice: Invoice, po: PurchaseOrder) -> ReconciliationResult:
        findings: list[ReconciliationFinding] = []

        if invoice.po_id != po.po_id:
            findings.append(
                ReconciliationFinding(
                    code="PO_ID_MISMATCH",
                    severity=RiskLevel.CRITICAL,
                    message="Invoice PO ID does not match purchase order.",
                    expected=po.po_id,
                    observed=invoice.po_id,
                )
            )

        if invoice.vendor_id != po.vendor_id:
            findings.append(
                ReconciliationFinding(
                    code="VENDOR_MISMATCH",
                    severity=RiskLevel.CRITICAL,
                    message="Invoice vendor differs from approved PO vendor.",
                    expected=po.vendor_id,
                    observed=invoice.vendor_id,
                )
            )

        if invoice.currency != po.currency:
            findings.append(
                ReconciliationFinding(
                    code="CURRENCY_MISMATCH",
                    severity=RiskLevel.HIGH,
                    message="Invoice and PO currencies differ.",
                    expected=po.currency,
                    observed=invoice.currency,
                )
            )

        variance = self._variance_percent(invoice.total, po.approved_total)
        if abs(variance) > self.amount_tolerance_percent:
            findings.append(
                ReconciliationFinding(
                    code="AMOUNT_VARIANCE",
                    severity=RiskLevel.HIGH if abs(variance) < 10 else RiskLevel.CRITICAL,
                    message="Invoice amount exceeds configured PO tolerance.",
                    expected=po.approved_total,
                    observed=invoice.total,
                )
            )

        if invoice.total > po.remaining_balance:
            findings.append(
                ReconciliationFinding(
                    code="INSUFFICIENT_PO_BALANCE",
                    severity=RiskLevel.CRITICAL,
                    message="Invoice total exceeds remaining PO balance.",
                    expected=po.remaining_balance,
                    observed=invoice.total,
                )
            )

        invoice_date = datetime.strptime(invoice.invoice_date, "%Y-%m-%d").date()
        valid_from = datetime.strptime(po.valid_from, "%Y-%m-%d").date()
        valid_to = datetime.strptime(po.valid_to, "%Y-%m-%d").date()
        if not (valid_from <= invoice_date <= valid_to):
            findings.append(
                ReconciliationFinding(
                    code="PO_DATE_WINDOW_VIOLATION",
                    severity=RiskLevel.HIGH,
                    message="Invoice date falls outside PO validity window.",
                    expected=f"{po.valid_from} to {po.valid_to}",
                    observed=invoice.invoice_date,
                )
            )

        line_variance = self._line_item_variance(invoice, po)
        if line_variance > self.amount_tolerance_percent:
            findings.append(
                ReconciliationFinding(
                    code="LINE_ITEM_VARIANCE",
                    severity=RiskLevel.MEDIUM,
                    message="Aggregated invoice line amount differs from PO line amount.",
                    expected="within tolerance",
                    observed=round(line_variance, 2),
                )
            )

        matched = not any(f.severity in {RiskLevel.HIGH, RiskLevel.CRITICAL} for f in findings)
        return ReconciliationResult(
            invoice_id=invoice.invoice_id,
            po_id=po.po_id,
            matched=matched,
            amount_variance_percent=round(variance, 3),
            findings=findings,
        )

    def _variance_percent(self, observed: float, expected: float) -> float:
        if expected == 0:
            return 100.0 if observed != 0 else 0.0
        return ((observed - expected) / expected) * 100.0

    def _line_item_variance(self, invoice: Invoice, po: PurchaseOrder) -> float:
        inv_amount = sum(item.amount for item in invoice.line_items)
        po_amount = sum(item.amount for item in po.line_items)
        return abs(self._variance_percent(inv_amount, po_amount)) if po_amount else 0.0
