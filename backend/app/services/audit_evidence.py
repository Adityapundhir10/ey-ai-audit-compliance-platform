from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy.orm import Session
from app.models import AuditEvent, InvoiceRecord
from app.schemas import ComplianceDecision, ExtractedInvoice, FraudScore, ReconciliationResult


class AuditTrailService:
    def record(self, db: Session, invoice_id: str, event_type: str, actor: str, decision: str, reason: str, evidence: Dict[str, Any]) -> AuditEvent:
        invoice = db.query(InvoiceRecord).filter(InvoiceRecord.invoice_id == invoice_id).first()
        event = AuditEvent(
            invoice_pk=invoice.id if invoice else None,
            invoice_id=invoice_id,
            event_type=event_type,
            actor=actor,
            decision=decision,
            reason=reason,
            evidence=evidence,
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event


class AuditEvidenceBuilder:
    def build(
        self,
        workflow_id: str,
        invoice: ExtractedInvoice,
        reconciliation: ReconciliationResult,
        compliance: ComplianceDecision,
        fraud: FraudScore,
        trace: dict,
    ) -> Dict[str, Any]:
        return {
            "workflow_id": workflow_id,
            "invoice_id": invoice.invoice_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "evidence_type": "invoice_compliance_audit_packet",
            "controls_tested": [
                "invoice_schema_validation",
                "po_three_way_match",
                "approval_threshold_check",
                "duplicate_invoice_screening",
                "vendor_risk_review",
                "policy_rag_citation_capture",
                "human_in_loop_escalation",
            ],
            "summary": {
                "invoice_total": invoice.total,
                "extraction_confidence": invoice.confidence,
                "po_matched": reconciliation.matched,
                "compliance_score": compliance.score,
                "fraud_score": fraud.score,
                "fraud_tier": fraud.risk_tier,
                "status": "approved" if compliance.compliant and fraud.score < 0.55 else "review_required",
            },
            "extraction": invoice.model_dump(),
            "reconciliation": reconciliation.model_dump(),
            "compliance": compliance.model_dump(),
            "fraud": fraud.model_dump(),
            "trace": trace,
        }
