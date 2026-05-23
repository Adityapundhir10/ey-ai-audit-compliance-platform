from __future__ import annotations
import math
from datetime import datetime
from typing import List
import numpy as np
from sklearn.ensemble import IsolationForest
from sqlalchemy.orm import Session
from app.models import InvoiceRecord, VendorRiskRecord
from app.schemas import ExtractedInvoice, FraudScore, FraudSignal


class VendorFeatureBuilder:
    def build(self, db: Session, invoice: ExtractedInvoice) -> dict:
        prior = db.query(InvoiceRecord).filter(InvoiceRecord.vendor_id == invoice.vendor_id).all()
        vendor = db.query(VendorRiskRecord).filter(VendorRiskRecord.vendor_id == invoice.vendor_id).first()
        duplicate_candidates = [
            inv for inv in prior
            if inv.invoice_id != invoice.invoice_id and abs(inv.total - invoice.total) < 1.0 and inv.po_number == invoice.po_number
        ]
        avg_amount = float(np.mean([inv.total for inv in prior])) if prior else invoice.total
        amount_z = (invoice.total - avg_amount) / max(float(np.std([inv.total for inv in prior])) if len(prior) > 1 else avg_amount * 0.15, 1.0)
        risk_tier = vendor.risk_tier if vendor else "unknown"
        risk_tier_value = {"low": 0.1, "medium": 0.35, "high": 0.7, "critical": 0.9}.get(risk_tier, 0.3)
        return {
            "prior_count": len(prior),
            "duplicate_count": len(duplicate_candidates),
            "avg_amount": avg_amount,
            "amount_z": float(amount_z),
            "risk_tier": risk_tier,
            "risk_tier_value": risk_tier_value,
            "historical_exception_rate": vendor.historical_exception_rate if vendor else 0.15,
            "late_submission_rate": vendor.late_submission_rate if vendor else 0.1,
        }


class FraudDetectionService:
    def __init__(self):
        self.feature_builder = VendorFeatureBuilder()

    def score(self, db: Session, invoice: ExtractedInvoice) -> FraudScore:
        features = self.feature_builder.build(db, invoice)
        signals: list[FraudSignal] = []
        duplicate_risk = min(1.0, features["duplicate_count"] / 2)
        amount_risk = min(1.0, max(0.0, abs(features["amount_z"]) / 4))
        vendor_risk = features["risk_tier_value"]
        extraction_risk = max(0.0, 1.0 - invoice.confidence)
        high_value_risk = 1.0 if invoice.total > 500000 else 0.45 if invoice.total > 100000 else 0.05

        signals.append(FraudSignal(name="duplicate_invoice", value=features["duplicate_count"], weight=0.28, description="Same PO and amount seen in previous invoices"))
        signals.append(FraudSignal(name="amount_outlier", value=round(features["amount_z"], 3), weight=0.22, description="Deviation from vendor historical average"))
        signals.append(FraudSignal(name="vendor_risk_tier", value=features["risk_tier"], weight=0.2, description="Vendor risk profile from master data"))
        signals.append(FraudSignal(name="extraction_uncertainty", value=round(extraction_risk, 3), weight=0.12, description="Low document extraction confidence"))
        signals.append(FraudSignal(name="high_value_invoice", value=invoice.total, weight=0.18, description="High value procurement transaction"))

        weighted = (
            duplicate_risk * 0.28
            + amount_risk * 0.22
            + vendor_risk * 0.2
            + extraction_risk * 0.12
            + high_value_risk * 0.18
        )
        isolation_component = self._isolation_forest_component(db, invoice, features)
        score = min(1.0, weighted * 0.75 + isolation_component * 0.25)
        if score >= 0.75:
            tier = "critical"
            action = "Block posting and escalate to internal audit."
        elif score >= 0.55:
            tier = "high"
            action = "Route to AP manager and procurement controller for review."
        elif score >= 0.35:
            tier = "medium"
            action = "Request supporting documents before posting."
        else:
            tier = "low"
            action = "Continue automated compliance workflow."
        return FraudScore(invoice_id=invoice.invoice_id, score=round(float(score), 3), risk_tier=tier, signals=signals, recommended_action=action)

    def _isolation_forest_component(self, db: Session, invoice: ExtractedInvoice, features: dict) -> float:
        rows = db.query(InvoiceRecord).all()
        if len(rows) < 5:
            return min(1.0, abs(features["amount_z"]) / 5)
        X = np.array([[r.total, r.risk_score, r.compliance_score, r.extraction_confidence] for r in rows], dtype=float)
        current = np.array([[invoice.total, 0.3, 0.8, invoice.confidence]], dtype=float)
        try:
            model = IsolationForest(contamination=0.12, random_state=42)
            model.fit(X)
            anomaly_score = -float(model.score_samples(current)[0])
            return min(1.0, max(0.0, (anomaly_score - 0.35) / 0.35))
        except Exception:
            return 0.0
