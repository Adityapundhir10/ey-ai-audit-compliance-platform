from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class InvoiceStatus(str, Enum):
    received = "received"
    extracted = "extracted"
    reconciled = "reconciled"
    exception = "exception"
    approval_required = "approval_required"
    approved = "approved"
    rejected = "rejected"
    posted = "posted"


class LineItem(BaseModel):
    description: str
    quantity: float = Field(ge=0)
    unit_price: float = Field(ge=0)
    amount: float = Field(ge=0)
    gl_code: Optional[str] = None
    cost_center: Optional[str] = None


class ExtractedInvoice(BaseModel):
    invoice_id: str
    vendor_id: str
    vendor_name: str
    po_number: str
    invoice_date: str
    due_date: str
    currency: str = "INR"
    subtotal: float = Field(ge=0)
    tax: float = Field(ge=0)
    total: float = Field(ge=0)
    line_items: List[LineItem] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source_document: Optional[str] = None

    @model_validator(mode="after")
    def validate_total(self):
        expected = round(self.subtotal + self.tax, 2)
        if abs(expected - round(self.total, 2)) > 1.0:
            raise ValueError(f"Invoice total mismatch: subtotal + tax = {expected}, total = {self.total}")
        return self


class InvoiceIngestRequest(BaseModel):
    raw_text: str = Field(min_length=20)
    source_document: Optional[str] = None
    run_workflow: bool = True


class WorkflowRunRequest(BaseModel):
    raw_text: Optional[str] = None
    invoice: Optional[ExtractedInvoice] = None
    source_document: Optional[str] = None
    simulate_human_approval: bool = True
    priority: str = "normal"


class ReconciliationResult(BaseModel):
    matched: bool
    po_number: str
    approved_amount: float = 0.0
    invoice_total: float = 0.0
    variance: float = 0.0
    variance_pct: float = 0.0
    reasons: List[str] = Field(default_factory=list)


class ComplianceDecision(BaseModel):
    compliant: bool
    score: float = Field(ge=0.0, le=1.0)
    policy_hits: List[Dict[str, Any]] = Field(default_factory=list)
    violations: List[str] = Field(default_factory=list)
    required_approvals: List[str] = Field(default_factory=list)
    explanation: str


class FraudSignal(BaseModel):
    name: str
    value: float | str | bool
    weight: float
    description: str


class FraudScore(BaseModel):
    invoice_id: str
    score: float = Field(ge=0.0, le=1.0)
    risk_tier: str
    signals: List[FraudSignal] = Field(default_factory=list)
    recommended_action: str


class RagQueryRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=15)
    filters: Dict[str, Any] = Field(default_factory=dict)


class RagQueryResponse(BaseModel):
    answer: str
    citations: List[Dict[str, Any]]
    confidence: float


class WorkflowRunResponse(BaseModel):
    workflow_id: str
    invoice_id: str
    status: str
    extraction: ExtractedInvoice
    reconciliation: ReconciliationResult
    compliance: ComplianceDecision
    fraud: FraudScore
    audit_evidence: Dict[str, Any]
    latency_ms: float
    trace_id: str


class AuditEventOut(BaseModel):
    invoice_id: str
    event_type: str
    actor: str
    decision: str
    reason: str
    evidence: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True
