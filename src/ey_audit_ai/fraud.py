from __future__ import annotations

import hashlib
import statistics
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from .schemas import FraudSignal, Invoice, RiskLevel, VendorProfile


class VendorRiskFeatureEngineer:
    def build_features(self, invoice: Invoice, vendor: VendorProfile, history: list[dict[str, Any]]) -> dict[str, float]:
        same_vendor = [row for row in history if row.get("vendor_id") == invoice.vendor_id]
        recent_90 = self._recent(same_vendor, invoice.invoice_date, days=90)
        values = [float(row.get("total", 0.0)) for row in same_vendor]
        recent_values = [float(row.get("total", 0.0)) for row in recent_90]
        return {
            "invoice_total": invoice.total,
            "vendor_avg_value": vendor.average_invoice_value,
            "value_to_vendor_avg_ratio": invoice.total / max(vendor.average_invoice_value, 1.0),
            "vendor_history_count": float(len(same_vendor)),
            "recent_90_count": float(len(recent_90)),
            "recent_90_total": sum(recent_values),
            "watchlist_flag": 1.0 if vendor.on_watchlist else 0.0,
            "risk_tier_score": {"low": 0.15, "medium": 0.45, "high": 0.75, "critical": 0.95}.get(vendor.risk_tier.lower(), 0.35),
            "robust_amount_z": self._robust_z(invoice.total, values),
        }

    def _recent(self, rows: list[dict[str, Any]], invoice_date: str, days: int) -> list[dict[str, Any]]:
        anchor = datetime.strptime(invoice_date, "%Y-%m-%d").date()
        cutoff = anchor - timedelta(days=days)
        out = []
        for row in rows:
            try:
                d = datetime.strptime(str(row.get("invoice_date")), "%Y-%m-%d").date()
                if cutoff <= d <= anchor:
                    out.append(row)
            except ValueError:
                continue
        return out

    def _robust_z(self, value: float, values: list[float]) -> float:
        if len(values) < 3:
            return 0.0
        med = statistics.median(values)
        deviations = [abs(v - med) for v in values]
        mad = statistics.median(deviations) or 1.0
        return abs(value - med) / (1.4826 * mad)


class ComplianceAnomalyEngine:
    """Fraud detection and compliance intelligence.

    Uses deterministic controls plus robust statistical features. Optional model
    adapters can be added in `score_with_ml_model` when labeled data is available.
    """

    def __init__(self):
        self.features = VendorRiskFeatureEngineer()

    def evaluate(self, invoice: Invoice, vendor: VendorProfile, history: list[dict[str, Any]]) -> tuple[float, list[FraudSignal]]:
        signals: list[FraudSignal] = []
        features = self.features.build_features(invoice, vendor, history)

        duplicate_score = self._duplicate_score(invoice, history)
        if duplicate_score > 0:
            signals.append(
                FraudSignal(
                    name="duplicate_invoice_risk",
                    score=duplicate_score,
                    severity=RiskLevel.HIGH if duplicate_score >= 0.75 else RiskLevel.MEDIUM,
                    explanation="Invoice resembles a historical invoice by vendor, amount, PO, or normalized document fingerprint.",
                )
            )

        if features["robust_amount_z"] >= 3.0:
            signals.append(
                FraudSignal(
                    name="amount_outlier",
                    score=min(features["robust_amount_z"] / 8.0, 1.0),
                    severity=RiskLevel.HIGH,
                    explanation="Invoice amount is a robust statistical outlier relative to vendor history.",
                )
            )

        if features["value_to_vendor_avg_ratio"] >= 2.5:
            signals.append(
                FraudSignal(
                    name="vendor_average_spike",
                    score=min(features["value_to_vendor_avg_ratio"] / 5.0, 1.0),
                    severity=RiskLevel.MEDIUM,
                    explanation="Invoice value materially exceeds the vendor average invoice value.",
                )
            )

        if vendor.on_watchlist:
            signals.append(
                FraudSignal(
                    name="watchlist_vendor",
                    score=0.90,
                    severity=RiskLevel.CRITICAL,
                    explanation="Vendor is marked as watchlist/high review in the vendor master.",
                )
            )

        rolling_score = min((features["recent_90_count"] / 20.0) + (features["recent_90_total"] / 250000.0), 1.0)
        if rolling_score >= 0.55:
            signals.append(
                FraudSignal(
                    name="rolling_window_concentration",
                    score=round(rolling_score, 3),
                    severity=RiskLevel.MEDIUM,
                    explanation="Recent invoice volume and value concentration for this vendor is elevated.",
                )
            )

        if not signals:
            signals.append(
                FraudSignal(
                    name="baseline_risk",
                    score=round(features["risk_tier_score"], 3),
                    severity=RiskLevel.LOW if features["risk_tier_score"] < 0.4 else RiskLevel.MEDIUM,
                    explanation="No major anomaly detected; vendor baseline risk contributes to final score.",
                )
            )

        combined = self._combine(signals)
        return combined, signals

    def _duplicate_score(self, invoice: Invoice, history: list[dict[str, Any]]) -> float:
        exact = 0.0
        near = 0.0
        this_fingerprint = self._fingerprint(invoice.vendor_id, invoice.po_id, invoice.total, invoice.invoice_date)
        for row in history:
            if row.get("invoice_id") == invoice.invoice_id:
                exact = max(exact, 1.0)
            if row.get("vendor_id") == invoice.vendor_id and abs(float(row.get("total", 0.0)) - invoice.total) < 1.0:
                near = max(near, 0.8)
            if row.get("po_id") == invoice.po_id and row.get("vendor_id") == invoice.vendor_id and abs(float(row.get("total", 0.0)) - invoice.total) / max(invoice.total, 1.0) < 0.01:
                near = max(near, 0.7)
            row_fp = self._fingerprint(str(row.get("vendor_id")), str(row.get("po_id")), float(row.get("total", 0.0)), str(row.get("invoice_date")))
            if row_fp == this_fingerprint:
                exact = max(exact, 0.95)
        return max(exact, near)

    def _fingerprint(self, vendor_id: str, po_id: str, total: float, invoice_date: str) -> str:
        body = f"{vendor_id}|{po_id}|{round(total, 2)}|{invoice_date}"
        return hashlib.sha256(body.encode()).hexdigest()[:16]

    def _combine(self, signals: list[FraudSignal]) -> float:
        complement = 1.0
        for signal in signals:
            complement *= 1.0 - min(max(signal.score, 0.0), 1.0)
        return round(1.0 - complement, 3)
