from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import AuditEvent, InvoiceRecord, PurchaseOrderRecord, VendorRiskRecord, WorkflowStateRecord
from app.schemas import AuditEventOut, FraudScore, RagQueryRequest, RagQueryResponse, WorkflowRunRequest, WorkflowRunResponse
from app.services.document_intelligence import InvoiceExtractor
from app.services.fraud_detection import FraudDetectionService
from app.services.rag import ComplianceRAGService, load_policy_documents
from app.services.workflow import InvoiceWorkflowEngine
from app.services.drift_monitor import DriftMonitor
from app.seed import seed_database

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "ey-ai-enterprise-audit-platform"}


@router.post("/demo/reset")
def demo_reset(db: Session = Depends(get_db)) -> dict:
    seed_database(db, reset=True)
    return {"status": "seeded"}


@router.get("/invoices")
def list_invoices(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(InvoiceRecord).order_by(InvoiceRecord.created_at.desc()).limit(50).all()
    return [
        {
            "invoice_id": r.invoice_id,
            "vendor": r.vendor_name,
            "po_number": r.po_number,
            "total": r.total,
            "status": r.status,
            "risk_score": r.risk_score,
            "compliance_score": r.compliance_score,
            "extraction_confidence": r.extraction_confidence,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: str, db: Session = Depends(get_db)) -> dict:
    r = db.query(InvoiceRecord).filter(InvoiceRecord.invoice_id == invoice_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {
        "invoice_id": r.invoice_id,
        "vendor_id": r.vendor_id,
        "vendor_name": r.vendor_name,
        "po_number": r.po_number,
        "invoice_date": r.invoice_date,
        "due_date": r.due_date,
        "currency": r.currency,
        "subtotal": r.subtotal,
        "tax": r.tax,
        "total": r.total,
        "status": r.status,
        "risk_score": r.risk_score,
        "compliance_score": r.compliance_score,
        "structured_payload": r.structured_payload,
    }


@router.post("/documents/extract")
async def extract_document(payload: dict) -> dict:
    raw_text = payload.get("raw_text", "")
    if len(raw_text) < 20:
        raise HTTPException(status_code=422, detail="raw_text must contain invoice content")
    invoice = await InvoiceExtractor().extract(raw_text, payload.get("source_document"))
    return invoice.model_dump()


@router.post("/workflows/run", response_model=WorkflowRunResponse)
async def run_workflow(request: WorkflowRunRequest, db: Session = Depends(get_db)) -> WorkflowRunResponse:
    if not request.raw_text and not request.invoice:
        raise HTTPException(status_code=422, detail="Provide either raw_text or invoice")
    return await InvoiceWorkflowEngine().run(db, request)


@router.get("/workflows")
def list_workflows(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(WorkflowStateRecord).order_by(WorkflowStateRecord.started_at.desc()).limit(50).all()
    return [
        {
            "workflow_id": r.workflow_id,
            "invoice_id": r.invoice_id,
            "status": r.status,
            "current_agent": r.current_agent,
            "started_at": r.started_at.isoformat(),
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        }
        for r in rows
    ]


@router.post("/rag/query", response_model=RagQueryResponse)
def rag_query(request: RagQueryRequest, db: Session = Depends(get_db)) -> RagQueryResponse:
    result = ComplianceRAGService(db).answer(request.query, request.top_k, request.filters)
    return RagQueryResponse(**result)


@router.post("/rag/reindex")
def rag_reindex(db: Session = Depends(get_db)) -> dict:
    count = load_policy_documents(db)
    return {"status": "indexed", "chunks": count}


@router.post("/fraud/score", response_model=FraudScore)
def fraud_score(payload: dict, db: Session = Depends(get_db)) -> FraudScore:
    from app.schemas import ExtractedInvoice
    invoice = ExtractedInvoice(**payload)
    return FraudDetectionService().score(db, invoice)


@router.get("/purchase-orders")
def list_purchase_orders(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(PurchaseOrderRecord).order_by(PurchaseOrderRecord.po_number).all()
    return [
        {
            "po_number": r.po_number,
            "vendor_id": r.vendor_id,
            "vendor_name": r.vendor_name,
            "department": r.department,
            "approved_amount": r.approved_amount,
            "currency": r.currency,
            "approved_by": r.approved_by,
            "active": r.active,
        }
        for r in rows
    ]


@router.get("/vendors/risk")
def list_vendor_risk(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(VendorRiskRecord).order_by(VendorRiskRecord.risk_tier.desc()).all()
    return [
        {
            "vendor_id": r.vendor_id,
            "vendor_name": r.vendor_name,
            "country": r.country,
            "risk_tier": r.risk_tier,
            "duplicate_rate": r.duplicate_rate,
            "late_submission_rate": r.late_submission_rate,
            "historical_exception_rate": r.historical_exception_rate,
            "average_invoice_amount": r.average_invoice_amount,
        }
        for r in rows
    ]


@router.get("/audit/events", response_model=list[AuditEventOut])
def audit_events(db: Session = Depends(get_db)) -> list[AuditEvent]:
    return db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(100).all()


@router.get("/audit/evidence/{invoice_id}")
def audit_evidence(invoice_id: str, db: Session = Depends(get_db)) -> dict:
    event = (
        db.query(AuditEvent)
        .filter(AuditEvent.invoice_id == invoice_id, AuditEvent.event_type == "audit_evidence_generated")
        .order_by(AuditEvent.created_at.desc())
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Audit evidence not found")
    return event.evidence


@router.get("/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db)) -> dict:
    invoices = db.query(InvoiceRecord).all()
    workflows = db.query(WorkflowStateRecord).all()
    risk_avg = sum(i.risk_score for i in invoices) / max(len(invoices), 1)
    compliance_avg = sum(i.compliance_score for i in invoices) / max(len(invoices), 1)
    review_required = len([i for i in invoices if i.status != "approved"])
    return {
        "invoice_count": len(invoices),
        "workflow_count": len(workflows),
        "review_required": review_required,
        "avg_risk_score": round(risk_avg, 3),
        "avg_compliance_score": round(compliance_avg, 3),
        "simulated_kpis": {
            "extraction_accuracy": 0.97,
            "fraud_roc_auc": 0.93,
            "false_positive_reduction": 0.34,
            "turnaround_time_reduction": 0.58,
            "inference_cost_reduction": 0.29,
        },
    }


@router.get("/observability/drift")
def drift_report(db: Session = Depends(get_db)) -> list[dict]:
    return [result.__dict__ for result in DriftMonitor().compute(db)]
