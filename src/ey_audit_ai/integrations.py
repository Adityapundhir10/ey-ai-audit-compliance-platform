from __future__ import annotations

import json
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator


@dataclass
class LLMUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0


class LiteLLMGateway:
    """Adapter boundary for LiteLLM/OpenAI/Azure OpenAI calls.

    Local mode uses deterministic extraction/routing and does not require API
    keys. When `enabled=True`, wire `litellm.completion` here and return a
    normalized response with usage data.
    """

    def __init__(self, enabled: bool = False, model: str = "gpt-4o-mini"):
        self.enabled = enabled
        self.model = model

    def structured_extract(self, prompt: str, schema: dict[str, Any]) -> tuple[dict[str, Any], LLMUsage]:
        start = time.perf_counter()
        if not self.enabled:
            return {"mode": "disabled", "reason": "deterministic local extractor is active"}, LLMUsage(latency_ms=(time.perf_counter() - start) * 1000)
        raise NotImplementedError("Install and configure LiteLLM before enabling LLM extraction.")

    def rerank(self, query: str, candidates: list[str]) -> tuple[list[int], LLMUsage]:
        start = time.perf_counter()
        ranked = list(range(len(candidates)))
        return ranked, LLMUsage(prompt_tokens=len(query.split()) + sum(len(c.split()) for c in candidates), latency_ms=(time.perf_counter() - start) * 1000)


class LangSmithTraceAdapter:
    """Adapter boundary for LangSmith traces and evaluation metadata."""

    def __init__(self, enabled: bool = False, project_name: str = "ey-audit-ai"):
        self.enabled = enabled
        self.project_name = project_name

    @contextmanager
    def span(self, name: str, **metadata: Any) -> Iterator[None]:
        if self.enabled:
            # Wire LangSmith client tracing here.
            pass
        yield


class KafkaAuditPublisher:
    """Publisher boundary for enterprise event streaming.

    Expected topics:
    - invoice.submitted
    - invoice.extracted
    - invoice.reconciled
    - invoice.risk_scored
    - invoice.approval_routed
    - audit.evidence.generated
    """

    def __init__(self, bootstrap_servers: str, enabled: bool = False):
        self.bootstrap_servers = bootstrap_servers
        self.enabled = enabled

    def publish(self, topic: str, event: dict[str, Any]) -> None:
        if not self.enabled:
            return
        raise NotImplementedError("Connect confluent-kafka or aiokafka here in production.")

    def serialize_event(self, event: dict[str, Any]) -> bytes:
        return json.dumps(event, default=str).encode("utf-8")
