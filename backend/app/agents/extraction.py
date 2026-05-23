from sqlalchemy.orm import Session
from app.agents.base import AgentContext, BaseAgent
from app.services.document_intelligence import InvoiceExtractor


class ExtractionAgent(BaseAgent):
    name = "extraction_agent"

    def __init__(self):
        self.extractor = InvoiceExtractor()

    async def run(self, db: Session, ctx: AgentContext) -> AgentContext:
        if ctx.get("invoice") is None:
            ctx["invoice"] = await self.extractor.extract(ctx["raw_text"], ctx.get("source_document"))
        return ctx
