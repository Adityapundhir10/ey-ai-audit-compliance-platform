from sqlalchemy.orm import Session
from app.agents.base import AgentContext, BaseAgent
from app.services.compliance_rules import ComplianceRuleEngine


class ComplianceAgent(BaseAgent):
    name = "compliance_agent"

    async def run(self, db: Session, ctx: AgentContext) -> AgentContext:
        engine = ComplianceRuleEngine(db)
        ctx["compliance"] = await engine.evaluate(ctx["invoice"], ctx["reconciliation"])
        return ctx
