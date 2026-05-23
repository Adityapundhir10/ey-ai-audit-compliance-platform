from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any


class WorkflowStatus(str, Enum):
    RECEIVED = "received"
    EXTRACTED = "extracted"
    RECONCILED = "reconciled"
    NEEDS_APPROVAL = "needs_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EVIDENCE_GENERATED = "evidence_generated"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class InvoiceLine:
    description: str
    quantity: float
    unit_price: float
    amount: float
    gl_code: str | None = None


@dataclass
class Invoice:
    invoice_id: str
    vendor_id: str
    vendor_name: str
    invoice_date: str
    due_date: str
    po_id: str
    currency: str
    subtotal: float
    tax: float
    total: float
    payment_terms: str
    line_items: list[InvoiceLine] = field(default_factory=list)
    source_document: str | None = None
    extracted_confidence: float = 0.0


@dataclass
class PurchaseOrder:
    po_id: str
    vendor_id: str
    currency: str
    approved_total: float
    remaining_balance: float
    valid_from: str
    valid_to: str
    cost_center: str
    approver_email: str
    status: str
    line_items: list[InvoiceLine] = field(default_factory=list)


@dataclass
class VendorProfile:
    vendor_id: str
    vendor_name: str
    risk_tier: str
    country: str
    average_invoice_value: float
    on_watchlist: bool = False


@dataclass
class ReconciliationFinding:
    code: str
    severity: RiskLevel
    message: str
    expected: Any | None = None
    observed: Any | None = None


@dataclass
class ReconciliationResult:
    invoice_id: str
    po_id: str
    matched: bool
    amount_variance_percent: float
    findings: list[ReconciliationFinding]


@dataclass
class FraudSignal:
    name: str
    score: float
    severity: RiskLevel
    explanation: str


@dataclass
class ComplianceFinding:
    policy_id: str
    title: str
    severity: RiskLevel
    message: str
    evidence_snippets: list[str]


@dataclass
class ApprovalDecision:
    route: str
    approver: str | None
    required: bool
    reason: str


@dataclass
class AuditEvidenceBundle:
    evidence_id: str
    invoice_id: str
    generated_at: str
    status: WorkflowStatus
    risk_score: float
    risk_level: RiskLevel
    reconciliation: ReconciliationResult
    fraud_signals: list[FraudSignal]
    compliance_findings: list[ComplianceFinding]
    approval: ApprovalDecision
    source_documents: list[str]
    workflow_trace: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WorkflowRequest:
    invoice_document_text: str
    purchase_order: dict[str, Any]
    vendor_profile: dict[str, Any]
    historical_invoices: list[dict[str, Any]] = field(default_factory=list)
