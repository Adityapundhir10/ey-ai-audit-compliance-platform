from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Iterable, List
import numpy as np
from sqlalchemy.orm import Session
from app.models import InvoiceRecord


@dataclass
class DriftResult:
    metric: str
    reference_mean: float
    current_mean: float
    psi: float
    status: str


class DriftMonitor:
    """Simple population stability monitor for invoice features.

    Production systems should use richer drift checks, segment-level analysis,
    alert routing, and model registry integration. This implementation is small
    enough for a portfolio repo but demonstrates the workflow.
    """

    def compute(self, db: Session) -> list[DriftResult]:
        rows = db.query(InvoiceRecord).order_by(InvoiceRecord.created_at.asc()).all()
        if len(rows) < 4:
            return []
        midpoint = max(2, len(rows) // 2)
        reference = rows[:midpoint]
        current = rows[midpoint:]
        return [
            self._psi_metric("invoice_total", [r.total for r in reference], [r.total for r in current]),
            self._psi_metric("risk_score", [r.risk_score for r in reference], [r.risk_score for r in current]),
            self._psi_metric("compliance_score", [r.compliance_score for r in reference], [r.compliance_score for r in current]),
            self._psi_metric("extraction_confidence", [r.extraction_confidence for r in reference], [r.extraction_confidence for r in current]),
        ]

    def _psi_metric(self, metric: str, reference: list[float], current: list[float], bins: int = 5) -> DriftResult:
        ref = np.array(reference, dtype=float)
        cur = np.array(current, dtype=float)
        if len(set(ref.tolist() + cur.tolist())) <= 1:
            psi = 0.0
        else:
            edges = np.quantile(ref, np.linspace(0, 1, bins + 1))
            edges = np.unique(edges)
            if len(edges) < 3:
                edges = np.linspace(min(ref.min(), cur.min()), max(ref.max(), cur.max()) + 1e-6, bins + 1)
            ref_hist, _ = np.histogram(ref, bins=edges)
            cur_hist, _ = np.histogram(cur, bins=edges)
            ref_pct = np.clip(ref_hist / max(ref_hist.sum(), 1), 1e-5, None)
            cur_pct = np.clip(cur_hist / max(cur_hist.sum(), 1), 1e-5, None)
            psi = float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))
        status = "stable" if psi < 0.1 else "watch" if psi < 0.25 else "drift_detected"
        return DriftResult(metric, float(ref.mean()), float(cur.mean()), round(psi, 4), status)
