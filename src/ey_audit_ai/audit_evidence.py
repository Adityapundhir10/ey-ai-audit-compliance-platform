from __future__ import annotations

import json
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .schemas import (
    ApprovalDecision,
    AuditEvidenceBundle,
    ComplianceFinding,
    FraudSignal,
    ReconciliationResult,
    RiskLevel,
    WorkflowStatus,
)


class EvidenceBundleWriter:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build_bundle(
        self,
        invoice_id: str,
        risk_score: float,
        reconciliation: ReconciliationResult,
        fraud_signals: list[FraudSignal],
        compliance_findings: list[ComplianceFinding],
        approval: ApprovalDecision,
        source_documents: list[str],
        workflow_trace: list[dict[str, Any]],
    ) -> AuditEvidenceBundle:
        risk_level = self._risk_level(risk_score)
        status = WorkflowStatus.NEEDS_APPROVAL if approval.required else WorkflowStatus.APPROVED
        return AuditEvidenceBundle(
            evidence_id=f"EVID-{uuid.uuid4().hex[:12].upper()}",
            invoice_id=invoice_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
            status=status,
            risk_score=risk_score,
            risk_level=risk_level,
            reconciliation=reconciliation,
            fraud_signals=fraud_signals,
            compliance_findings=compliance_findings,
            approval=approval,
            source_documents=source_documents,
            workflow_trace=workflow_trace,
        )

    def write(self, bundle: AuditEvidenceBundle) -> Path:
        path = self.output_dir / f"{bundle.evidence_id}_{bundle.invoice_id}.json"
        path.write_text(json.dumps(bundle.to_dict(), indent=2, default=str), encoding="utf-8")
        markdown_path = self.output_dir / f"{bundle.evidence_id}_{bundle.invoice_id}.md"
        markdown_path.write_text(self.to_markdown(bundle), encoding="utf-8")
        return path

    def to_markdown(self, bundle: AuditEvidenceBundle) -> str:
        lines = [
            f"# Audit Evidence Bundle {bundle.evidence_id}",
            "",
            f"- Invoice: `{bundle.invoice_id}`",
            f"- Generated: `{bundle.generated_at}`",
            f"- Status: `{bundle.status.value}`",
            f"- Risk score: `{bundle.risk_score}` ({bundle.risk_level.value})",
            "",
            "## Reconciliation",
            f"- PO: `{bundle.reconciliation.po_id}`",
            f"- Matched: `{bundle.reconciliation.matched}`",
            f"- Amount variance: `{bundle.reconciliation.amount_variance_percent}%`",
            "",
            "### Reconciliation findings",
        ]
        for finding in bundle.reconciliation.findings:
            lines.append(f"- **{finding.code}** ({finding.severity.value}): {finding.message}")
        lines.extend(["", "## Fraud signals"])
        for signal in bundle.fraud_signals:
            lines.append(f"- **{signal.name}** score={signal.score} severity={signal.severity.value}: {signal.explanation}")
        lines.extend(["", "## Compliance findings"])
        for finding in bundle.compliance_findings:
            lines.append(f"- **{finding.title}** ({finding.severity.value}): {finding.message}")
        lines.extend(["", "## Approval", f"- Route: `{bundle.approval.route}`", f"- Required: `{bundle.approval.required}`", f"- Approver: `{bundle.approval.approver}`", f"- Reason: {bundle.approval.reason}"])
        return "\n".join(lines) + "\n"

    def _risk_level(self, score: float) -> RiskLevel:
        if score >= 0.85:
            return RiskLevel.CRITICAL
        if score >= 0.65:
            return RiskLevel.HIGH
        if score >= 0.35:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW
