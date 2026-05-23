from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator

try:
    from prometheus_client import Counter, Gauge, Histogram, generate_latest
except Exception:  # pragma: no cover
    Counter = Gauge = Histogram = None

    def generate_latest():
        return b"prometheus_client_not_installed 1\n"


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("ey_audit_ai")


@dataclass
class WorkflowTrace:
    events: list[dict[str, Any]] = field(default_factory=list)

    def add(self, stage: str, status: str, **attrs: Any) -> None:
        self.events.append({"stage": stage, "status": status, "ts": time.time(), **attrs})


class Metrics:
    def __init__(self) -> None:
        if Counter:
            self.workflow_runs = Counter("workflow_runs_total", "Total workflow runs", ["status"])
            self.agent_latency = Histogram("agent_latency_seconds", "Agent stage latency", ["agent"])
            self.risk_score = Gauge("invoice_risk_score", "Latest invoice risk score", ["invoice_id"])
            self.approvals = Counter("approval_routes_total", "Approval routes", ["route"])
        else:
            self.workflow_runs = self.agent_latency = self.risk_score = self.approvals = None

    @contextmanager
    def time_agent(self, agent: str) -> Iterator[None]:
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            if self.agent_latency:
                self.agent_latency.labels(agent=agent).observe(elapsed)
            logger.info("agent_latency", extra={"agent": agent, "elapsed": elapsed})

    def mark_run(self, status: str) -> None:
        if self.workflow_runs:
            self.workflow_runs.labels(status=status).inc()

    def set_risk(self, invoice_id: str, score: float) -> None:
        if self.risk_score:
            self.risk_score.labels(invoice_id=invoice_id).set(score)

    def mark_route(self, route: str) -> None:
        if self.approvals:
            self.approvals.labels(route=route).inc()

    def render_prometheus(self) -> bytes:
        return generate_latest()


metrics = Metrics()
