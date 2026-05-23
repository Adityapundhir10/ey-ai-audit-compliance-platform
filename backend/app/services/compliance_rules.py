from sqlalchemy.orm import Session
from app.schemas import ComplianceDecision, ExtractedInvoice, ReconciliationResult
from app.services.rag import ComplianceRAGService
from app.services.llm_gateway import LLMGateway


class ComplianceRuleEngine:
    def __init__(self, db: Session):
        self.db = db
        self.rag = ComplianceRAGService(db)
        self.llm = LLMGateway()

    async def evaluate(self, invoice: ExtractedInvoice, reconciliation: ReconciliationResult) -> ComplianceDecision:
        violations: list[str] = []
        required_approvals: list[str] = []

        rag_result = self.rag.answer(
            query=f"invoice approval threshold vendor risk po reconciliation duplicate payment {invoice.currency} {invoice.total}",
            top_k=4,
        )

        if not reconciliation.matched:
            violations.extend(reconciliation.reasons)
            required_approvals.append("AP Manager")
        if invoice.total > 100000:
            required_approvals.extend(["Finance Controller", "Procurement Head"])
        if invoice.total > 500000:
            violations.append("High-value invoice requires enhanced audit sampling")
            required_approvals.append("Internal Audit Lead")
        if invoice.confidence < 0.85:
            violations.append("Document extraction confidence below automated posting threshold")
            required_approvals.append("Document Review Analyst")
        if not invoice.line_items:
            violations.append("No line-item evidence extracted")

        score = 1.0
        score -= 0.18 * len(violations)
        score -= 0.08 * max(0, len(required_approvals) - 1)
        score = max(0.0, min(1.0, score))
        explanation = await self.llm.compliance_explanation(invoice.model_dump(), violations, rag_result["citations"])
        return ComplianceDecision(
            compliant=len(violations) == 0,
            score=round(score, 3),
            policy_hits=rag_result["citations"],
            violations=violations,
            required_approvals=sorted(set(required_approvals)),
            explanation=explanation,
        )
