from __future__ import annotations
from dataclasses import dataclass, asdict
from sqlalchemy.orm import Session
from app.models import InvoiceRecord, VendorRiskRecord
from app.schemas import ExtractedInvoice


@dataclass
class InvoiceFeatureVector:
    invoice_id: str
    vendor_id: str
    amount: float
    tax_rate: float
    vendor_risk_numeric: float
    historical_invoice_count: int
    vendor_average_amount: float
    amount_to_vendor_average_ratio: float
    extraction_confidence: float

    def to_dict(self):
        return asdict(self)


class FeatureStore:
    """Feature materialization layer for fraud and compliance models."""

    def materialize_invoice_features(self, db: Session, invoice: ExtractedInvoice) -> InvoiceFeatureVector:
        vendor = db.query(VendorRiskRecord).filter(VendorRiskRecord.vendor_id == invoice.vendor_id).first()
        historical = db.query(InvoiceRecord).filter(InvoiceRecord.vendor_id == invoice.vendor_id).all()
        avg = vendor.average_invoice_amount if vendor else (sum(x.total for x in historical) / max(len(historical), 1) if historical else invoice.total)
        risk_numeric = {"low": 0.1, "medium": 0.35, "high": 0.7, "critical": 0.95}.get(vendor.risk_tier if vendor else "medium", 0.35)
        return InvoiceFeatureVector(
            invoice_id=invoice.invoice_id,
            vendor_id=invoice.vendor_id,
            amount=invoice.total,
            tax_rate=round(invoice.tax / max(invoice.subtotal, 1.0), 4),
            vendor_risk_numeric=risk_numeric,
            historical_invoice_count=len(historical),
            vendor_average_amount=avg,
            amount_to_vendor_average_ratio=round(invoice.total / max(avg, 1.0), 4),
            extraction_confidence=invoice.confidence,
        )
