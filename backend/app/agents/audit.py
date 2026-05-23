from sqlalchemy.orm import Session
from app.agents.base import AgentContext, BaseAgent
from app.services.audit_evidence import AuditEvidenceBuilder, AuditTrailService


class AuditEvidenceAgent(BaseAgent):
    name = "audit_evidence_agent"

    def __init__(self):
        self.builder = AuditEvidenceBuilder()
        self.trail = AuditTrailService()

    async def run(self, db: Session, ctx: AgentContext) -> AgentContext:
        packet = self.builder.build(
            workflow_id=ctx["workflow_id"],
            invoice=ctx["invoice"],
            reconciliation=ctx["reconciliation"],
            compliance=ctx["compliance"],
            fraud=ctx["fraud"],
            trace=ctx.get("trace", {}),
        )
        packet["approval"] = ctx.get("approval", {})
        ctx["audit_evidence"] = packet
        self.trail.record(
            db,
            invoice_id=ctx["invoice"].invoice_id,
            event_type="audit_evidence_generated",
            actor="audit_evidence_agent",
            decision=packet["summary"]["status"],
            reason="Generated structured audit packet with policy citations and risk signals.",
            evidence=packet,
        )
        return ctx
