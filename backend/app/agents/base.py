from abc import ABC, abstractmethod
from typing import Any, Dict
from sqlalchemy.orm import Session
from app.observability import AGENT_COUNTER


class AgentContext(Dict[str, Any]):
    pass


class BaseAgent(ABC):
    name: str = "base_agent"

    async def __call__(self, db: Session, ctx: AgentContext) -> AgentContext:
        try:
            result = await self.run(db, ctx)
            AGENT_COUNTER.labels(agent=self.name, status="ok").inc()
            return result
        except Exception as exc:
            AGENT_COUNTER.labels(agent=self.name, status="error").inc()
            ctx.setdefault("errors", []).append({"agent": self.name, "error": str(exc)})
            raise

    @abstractmethod
    async def run(self, db: Session, ctx: AgentContext) -> AgentContext:
        raise NotImplementedError
