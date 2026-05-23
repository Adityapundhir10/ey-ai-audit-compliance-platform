import json
from typing import Any, Dict
from app.core.config import get_settings
from app.observability import LLM_COUNTER


class LLMGateway:
    """LiteLLM-style abstraction.

    In production you can call LiteLLM/OpenAI/Azure OpenAI here. For portfolio use,
    this deterministic local fallback keeps the project runnable without paid APIs.
    """

    def __init__(self):
        self.settings = get_settings()

    async def structured_extract(self, prompt: str, schema_hint: Dict[str, Any]) -> Dict[str, Any]:
        LLM_COUNTER.labels(provider=self.settings.llm_provider, status="fallback").inc()
        return {
            "provider": self.settings.llm_provider,
            "mode": "deterministic_fallback",
            "schema_keys": list(schema_hint.keys()),
            "notes": "No external LLM configured; regex/OCR pipeline provided the structured fields.",
        }

    async def compliance_explanation(self, invoice: Dict[str, Any], violations: list[str], citations: list[dict]) -> str:
        LLM_COUNTER.labels(provider=self.settings.llm_provider, status="fallback").inc()
        if not violations:
            return "Invoice passed deterministic policy checks and matched the purchase order within tolerance."
        return "Invoice requires review because: " + "; ".join(violations) + ". Evidence citations were attached to the audit trail."

    async def summarize_audit_packet(self, packet: Dict[str, Any]) -> str:
        LLM_COUNTER.labels(provider=self.settings.llm_provider, status="fallback").inc()
        invoice_id = packet.get("invoice_id", "unknown")
        return f"Audit packet for {invoice_id}: extraction, reconciliation, compliance, fraud, and approval evidence are preserved with timestamps."
