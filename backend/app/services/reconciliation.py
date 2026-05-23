from sqlalchemy.orm import Session
from app.models import PurchaseOrderRecord
from app.schemas import ExtractedInvoice, ReconciliationResult


class POReconciliationService:
    def __init__(self, tolerance_pct: float = 2.0, tolerance_abs: float = 500.0):
        self.tolerance_pct = tolerance_pct
        self.tolerance_abs = tolerance_abs

    def reconcile(self, db: Session, invoice: ExtractedInvoice) -> ReconciliationResult:
        po = db.query(PurchaseOrderRecord).filter(PurchaseOrderRecord.po_number == invoice.po_number).first()
        reasons: list[str] = []
        if not po:
            return ReconciliationResult(
                matched=False,
                po_number=invoice.po_number,
                approved_amount=0.0,
                invoice_total=invoice.total,
                variance=invoice.total,
                variance_pct=100.0,
                reasons=["Purchase order not found"],
            )

        if not po.active:
            reasons.append("Purchase order is inactive")
        if po.vendor_id != invoice.vendor_id:
            reasons.append(f"Vendor mismatch: PO vendor {po.vendor_id}, invoice vendor {invoice.vendor_id}")
        if po.currency != invoice.currency:
            reasons.append(f"Currency mismatch: PO {po.currency}, invoice {invoice.currency}")

        variance = round(invoice.total - po.approved_amount, 2)
        variance_pct = round((variance / max(po.approved_amount, 1.0)) * 100, 2)
        if abs(variance) > self.tolerance_abs and abs(variance_pct) > self.tolerance_pct:
            reasons.append(f"Amount variance {variance_pct}% exceeds tolerance")

        matched = len(reasons) == 0
        return ReconciliationResult(
            matched=matched,
            po_number=invoice.po_number,
            approved_amount=po.approved_amount,
            invoice_total=invoice.total,
            variance=variance,
            variance_pct=variance_pct,
            reasons=reasons,
        )
