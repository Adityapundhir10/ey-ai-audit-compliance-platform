from sqlalchemy.orm import Session
from app.agents.base import AgentContext, BaseAgent


class IntakeAgent(BaseAgent):
    name = "intake_agent"

    async def run(self, db: Session, ctx: AgentContext) -> AgentContext:
        ctx["priority"] = ctx.get("priority", "normal")
        ctx["intake_checks"] = {
            "has_raw_text": bool(ctx.get("raw_text")),
            "has_invoice_object": bool(ctx.get("invoice")),
            "source_document": ctx.get("source_document"),
        }
        return ctx
