from __future__ import annotations
import time
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.agents.audit import AuditEvidenceAgent
from app.agents.approval import HumanApprovalAgent
from app.agents.compliance import ComplianceAgent
from app.agents.extraction import ExtractionAgent
from app.agents.fraud import FraudAgent
from app.agents.intake import IntakeAgent
from app.agents.reconciliation import ReconciliationAgent
from app.models import InvoiceRecord, WorkflowStateRecord
from app.observability import EXTRACTION_CONFIDENCE, FRAUD_SCORE_GAUGE, WORKFLOW_COUNTER, TraceContext, workflow_timer
from app.schemas import ExtractedInvoice, WorkflowRunRequest, WorkflowRunResponse


class InvoiceWorkflowEngine:
    """LangGraph-style deterministic state machine.

    The class has explicit nodes, conditional routing, persistent workflow state,
    retry-ready context, and audit event output. If real LangGraph is installed,
    you can map these same nodes to StateGraph without changing service logic.
    """

    def __init__(self):
        self.intake = IntakeAgent()
        self.extraction = ExtractionAgent()
        self.reconciliation = ReconciliationAgent()
        self.compliance = ComplianceAgent()
        self.fraud = FraudAgent()
        self.approval = HumanApprovalAgent()
        self.audit = AuditEvidenceAgent()

    async def run(self, db: Session, request: WorkflowRunRequest) -> WorkflowRunResponse:
        started = time.perf_counter()
        workflow_id = f"WF-{uuid.uuid4().hex[:10].upper()}"
        trace = TraceContext("invoice_compliance_workflow", {"workflow_id": workflow_id})
        ctx = {
            "workflow_id": workflow_id,
            "raw_text": request.raw_text,
            "invoice": request.invoice,
            "source_document": request.source_document,
            "simulate_human_approval": request.simulate_human_approval,
            "priority": request.priority,
            "trace": {"trace_id": trace.trace_id},
        }

        with workflow_timer():
            try:
                for agent in [self.intake, self.extraction, self.reconciliation, self.compliance, self.fraud]:
                    trace.add_event("agent_started", agent=agent.name)
                    ctx = await agent(db, ctx)
                    trace.add_event("agent_finished", agent=agent.name)
                    self._persist_state(db, workflow_id, ctx, status="running", current_agent=agent.name)

                if self._needs_approval(ctx):
                    trace.add_event("conditional_route", to="human_approval_agent", reason="policy_or_fraud_threshold")
                    ctx = await self.approval(db, ctx)
                else:
                    ctx["approval"] = {"required": False, "approvers": [], "status": "auto_approved", "conditions": []}

                trace_payload = trace.finish("ok")
                ctx["trace"] = trace_payload
                ctx = await self.audit(db, ctx)
                self._upsert_invoice(db, ctx)
                self._persist_state(db, workflow_id, ctx, status="completed", current_agent="audit_evidence_agent", completed=True)
                WORKFLOW_COUNTER.labels(status="completed").inc()
            except Exception:
                WORKFLOW_COUNTER.labels(status="failed").inc()
                self._persist_state(db, workflow_id, ctx, status="failed", current_agent="error")
                raise

        invoice = ctx["invoice"]
        fraud = ctx["fraud"]
        EXTRACTION_CONFIDENCE.labels(invoice_id=invoice.invoice_id).set(invoice.confidence)
        FRAUD_SCORE_GAUGE.labels(invoice_id=invoice.invoice_id).set(fraud.score)
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        status = ctx["audit_evidence"]["summary"]["status"]
        return WorkflowRunResponse(
            workflow_id=workflow_id,
            invoice_id=invoice.invoice_id,
            status=status,
            extraction=invoice,
            reconciliation=ctx["reconciliation"],
            compliance=ctx["compliance"],
            fraud=fraud,
            audit_evidence=ctx["audit_evidence"],
            latency_ms=latency_ms,
            trace_id=trace.trace_id,
        )

    def _needs_approval(self, ctx: dict) -> bool:
        return bool(ctx["compliance"].required_approvals) or ctx["fraud"].score >= 0.35 or not ctx["reconciliation"].matched

    def _upsert_invoice(self, db: Session, ctx: dict) -> None:
        invoice: ExtractedInvoice = ctx["invoice"]
        existing = db.query(InvoiceRecord).filter(InvoiceRecord.invoice_id == invoice.invoice_id).first()
        payload = {
            "invoice_id": invoice.invoice_id,
            "vendor_id": invoice.vendor_id,
            "vendor_name": invoice.vendor_name,
            "po_number": invoice.po_number,
            "invoice_date": invoice.invoice_date,
            "due_date": invoice.due_date,
            "currency": invoice.currency,
            "subtotal": invoice.subtotal,
            "tax": invoice.tax,
            "total": invoice.total,
            "status": ctx["audit_evidence"]["summary"]["status"],
            "risk_score": ctx["fraud"].score,
            "compliance_score": ctx["compliance"].score,
            "extraction_confidence": invoice.confidence,
            "raw_text": ctx.get("raw_text") or "",
            "structured_payload": invoice.model_dump(),
        }
        if existing:
            for k, v in payload.items():
                setattr(existing, k, v)
        else:
            db.add(InvoiceRecord(**payload))
        db.commit()

    def _persist_state(self, db: Session, workflow_id: str, ctx: dict, status: str, current_agent: str, completed: bool = False) -> None:
        invoice_id = ctx.get("invoice").invoice_id if ctx.get("invoice") else "pending"
        safe_payload = {}
        for k, v in ctx.items():
            if hasattr(v, "model_dump"):
                safe_payload[k] = v.model_dump()
            elif k not in {"raw_text"}:
                safe_payload[k] = v
        record = db.query(WorkflowStateRecord).filter(WorkflowStateRecord.workflow_id == workflow_id).first()
        if record:
            record.status = status
            record.current_agent = current_agent
            record.invoice_id = invoice_id
            record.state_payload = safe_payload
            if completed:
                record.completed_at = datetime.utcnow()
        else:
            db.add(WorkflowStateRecord(workflow_id=workflow_id, invoice_id=invoice_id, status=status, current_agent=current_agent, state_payload=safe_payload))
        db.commit()
