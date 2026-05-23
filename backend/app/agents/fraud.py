from sqlalchemy.orm import Session
from app.agents.base import AgentContext, BaseAgent
from app.services.fraud_detection import FraudDetectionService


class FraudAgent(BaseAgent):
    name = "fraud_agent"

    def __init__(self):
        self.service = FraudDetectionService()

    async def run(self, db: Session, ctx: AgentContext) -> AgentContext:
        ctx["fraud"] = self.service.score(db, ctx["invoice"])
        return ctx
