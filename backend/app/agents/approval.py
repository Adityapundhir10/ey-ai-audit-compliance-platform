from sqlalchemy.orm import Session
from app.agents.base import AgentContext, BaseAgent


class HumanApprovalAgent(BaseAgent):
    name = "human_approval_agent"

    async def run(self, db: Session, ctx: AgentContext) -> AgentContext:
        compliance = ctx["compliance"]
        fraud = ctx["fraud"]
        needs_approval = bool(compliance.required_approvals) or fraud.score >= 0.35
        simulated = ctx.get("simulate_human_approval", True)
        if needs_approval:
            ctx["approval"] = {
                "required": True,
                "approvers": compliance.required_approvals or ["AP Manager"],
                "status": "approved_with_conditions" if simulated and fraud.score < 0.75 else "pending_manual_review",
                "conditions": [fraud.recommended_action],
            }
        else:
            ctx["approval"] = {"required": False, "approvers": [], "status": "auto_approved", "conditions": []}
        return ctx
