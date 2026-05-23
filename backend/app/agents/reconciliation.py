from sqlalchemy.orm import Session
from app.agents.base import AgentContext, BaseAgent
from app.services.reconciliation import POReconciliationService


class ReconciliationAgent(BaseAgent):
    name = "reconciliation_agent"

    def __init__(self):
        self.service = POReconciliationService()

    async def run(self, db: Session, ctx: AgentContext) -> AgentContext:
        ctx["reconciliation"] = self.service.reconcile(db, ctx["invoice"])
        return ctx
