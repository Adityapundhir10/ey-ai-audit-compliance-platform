from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from .audit_evidence import EvidenceBundleWriter
from .config import settings
from .document_intelligence import SchemaConstrainedInvoiceExtractor
from .fraud import ComplianceAnomalyEngine
from .observability import WorkflowTrace, metrics
from .rag import HybridPolicyRetriever, PolicyChunker
from .reconciliation import POReconciler
from .schemas import (
    ApprovalDecision,
    ComplianceFinding,
    Invoice,
    PurchaseOrder,
    ReconciliationResult,
    RiskLevel,
    VendorProfile,
)


class ExtractionAgent:
    def __init__(self):
        self.extractor = SchemaConstrainedInvoiceExtractor()

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        invoice = self.extractor.extract(state["invoice_document_text"], source_document="request_payload")
        state["invoice"] = invoice
        state["trace"].add("extraction_agent", "ok", invoice_id=invoice.invoice_id, confidence=invoice.extracted_confidence)
        return state


class ReconciliationAgent:
    def __init__(self, amount_tolerance_percent: float | None = None):
        self.reconciler = POReconciler(amount_tolerance_percent=amount_tolerance_percent or settings.amount_tolerance_percent)

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        po = self._parse_po(state["purchase_order"])
        result = self.reconciler.reconcile(state["invoice"], po)
        state["purchase_order_obj"] = po
        state["reconciliation"] = result
        state["trace"].add("reconciliation_agent", "ok", matched=result.matched, findings=len(result.findings))
        return state

    def _parse_po(self, payload: dict[str, Any]) -> PurchaseOrder:
        from .schemas import InvoiceLine

        line_items = [InvoiceLine(**item) for item in payload.get("line_items", [])]
        return PurchaseOrder(
            po_id=payload["po_id"],
            vendor_id=payload["vendor_id"],
            currency=payload["currency"],
            approved_total=float(payload["approved_total"]),
            remaining_balance=float(payload["remaining_balance"]),
            valid_from=payload["valid_from"],
            valid_to=payload["valid_to"],
            cost_center=payload["cost_center"],
            approver_email=payload["approver_email"],
            status=payload["status"],
            line_items=line_items,
        )


class ComplianceRAGAgent:
    def __init__(self, policy_docs_path: Path | None = None):
        chunks = PolicyChunker().chunk_directory(policy_docs_path or settings.policy_docs_path)
        self.retriever = HybridPolicyRetriever(chunks)

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        invoice: Invoice = state["invoice"]
        query = self._build_query(state)
        hits = self.retriever.retrieve(query, top_k=4)
        findings = self._findings(invoice, state["reconciliation"], hits)
        state["policy_hits"] = hits
        state["compliance_findings"] = findings
        state["trace"].add("compliance_rag_agent", "ok", hits=len(hits), findings=len(findings))
        return state

    def _build_query(self, state: dict[str, Any]) -> str:
        invoice: Invoice = state["invoice"]
        reconciliation: ReconciliationResult = state["reconciliation"]
        finding_terms = " ".join(f.code for f in reconciliation.findings)
        return f"invoice approval duplicate po tax watchlist threshold evidence {invoice.total} {invoice.currency} {finding_terms}"

    def _findings(self, invoice: Invoice, reconciliation: ReconciliationResult, hits: list[Any]) -> list[ComplianceFinding]:
        findings: list[ComplianceFinding] = []
        snippets = [h.chunk.text[:240].replace("\n", " ") for h in hits[:2]]
        if not reconciliation.matched:
            findings.append(
                ComplianceFinding(
                    policy_id="PO-RECON-001",
                    title="PO reconciliation exception",
                    severity=RiskLevel.HIGH,
                    message="Invoice has reconciliation exceptions that require audit review before payment release.",
                    evidence_snippets=snippets,
                )
            )
        if invoice.total >= settings.high_value_invoice_threshold:
            findings.append(
                ComplianceFinding(
                    policy_id="APPROVAL-THRESHOLD-002",
                    title="High-value invoice approval",
                    severity=RiskLevel.MEDIUM,
                    message="Invoice exceeds the configured high-value threshold and must route to finance controller approval.",
                    evidence_snippets=snippets,
                )
            )
        return findings


class FraudAgent:
    def __init__(self):
        self.engine = ComplianceAnomalyEngine()

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        vendor = VendorProfile(**state["vendor_profile"])
        risk_score, signals = self.engine.evaluate(state["invoice"], vendor, state.get("historical_invoices", []))
        state["vendor_profile_obj"] = vendor
        state["risk_score"] = risk_score
        state["fraud_signals"] = signals
        metrics.set_risk(state["invoice"].invoice_id, risk_score)
        state["trace"].add("fraud_agent", "ok", risk_score=risk_score, signals=len(signals))
        return state


class ApprovalRouterAgent:
    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        invoice: Invoice = state["invoice"]
        po: PurchaseOrder = state["purchase_order_obj"]
        risk = state["risk_score"]
        compliance_count = len(state.get("compliance_findings", []))
        recon_critical = any(f.severity == RiskLevel.CRITICAL for f in state["reconciliation"].findings)

        if recon_critical or risk >= 0.85:
            decision = ApprovalDecision(
                route="audit_partner_review",
                approver="audit-partner@example.com",
                required=True,
                reason="Critical reconciliation or fraud risk detected.",
            )
        elif risk >= settings.risk_approval_threshold or compliance_count > 0 or invoice.total >= settings.high_value_invoice_threshold:
            decision = ApprovalDecision(
                route="finance_controller_approval",
                approver=po.approver_email,
                required=True,
                reason="High-value invoice, risk threshold, or compliance exception requires human approval.",
            )
        else:
            decision = ApprovalDecision(
                route="auto_approve",
                approver=None,
                required=False,
                reason="Invoice passed automated checks within risk tolerance.",
            )
        state["approval"] = decision
        metrics.mark_route(decision.route)
        state["trace"].add("approval_router_agent", "ok", route=decision.route, required=decision.required)
        return state


class EvidenceAgent:
    def __init__(self, output_dir: Path | None = None):
        self.writer = EvidenceBundleWriter(output_dir or settings.evidence_output_dir)

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        invoice: Invoice = state["invoice"]
        bundle = self.writer.build_bundle(
            invoice_id=invoice.invoice_id,
            risk_score=state["risk_score"],
            reconciliation=state["reconciliation"],
            fraud_signals=state["fraud_signals"],
            compliance_findings=state["compliance_findings"],
            approval=state["approval"],
            source_documents=[invoice.source_document or "unknown"],
            workflow_trace=state["trace"].events,
        )
        evidence_path = self.writer.write(bundle)
        state["evidence_bundle"] = bundle
        state["evidence_path"] = str(evidence_path)
        state["trace"].add("evidence_agent", "ok", evidence_id=bundle.evidence_id, path=str(evidence_path))
        return state


class MultiAgentInvoiceAuditGraph:
    """LangGraph-style sequential graph with explicit state transitions."""

    def __init__(self):
        self.agents = [
            ("extraction", ExtractionAgent()),
            ("reconciliation", ReconciliationAgent(settings.amount_tolerance_percent)),
            ("compliance_rag", ComplianceRAGAgent(settings.policy_docs_path)),
            ("fraud", FraudAgent()),
            ("approval", ApprovalRouterAgent()),
            ("evidence", EvidenceAgent(settings.evidence_output_dir)),
        ]

    def run(self, request: dict[str, Any]) -> dict[str, Any]:
        trace = WorkflowTrace()
        state: dict[str, Any] = {**request, "trace": trace}
        trace.add("workflow", "started")
        try:
            for agent_name, agent in self.agents:
                with metrics.time_agent(agent_name):
                    state = agent.run(state)
            trace.add("workflow", "completed")
            metrics.mark_run("success")
            return self._public_response(state)
        except Exception as exc:
            trace.add("workflow", "failed", error=str(exc))
            metrics.mark_run("failed")
            raise

    def _public_response(self, state: dict[str, Any]) -> dict[str, Any]:
        bundle = state["evidence_bundle"]
        return {
            "invoice": asdict(state["invoice"]),
            "risk_score": state["risk_score"],
            "approval": asdict(state["approval"]),
            "reconciliation": asdict(state["reconciliation"]),
            "fraud_signals": [asdict(s) for s in state["fraud_signals"]],
            "compliance_findings": [asdict(f) for f in state["compliance_findings"]],
            "evidence_id": bundle.evidence_id,
            "evidence_path": state["evidence_path"],
            "workflow_trace": state["trace"].events,
        }
