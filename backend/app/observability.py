import time
import uuid
from contextlib import contextmanager
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

WORKFLOW_COUNTER = Counter("ey_workflow_runs_total", "Total workflow runs", ["status"])
AGENT_COUNTER = Counter("ey_agent_invocations_total", "Total agent invocations", ["agent", "status"])
LLM_COUNTER = Counter("ey_llm_calls_total", "Total LLM calls", ["provider", "status"])
FRAUD_SCORE_GAUGE = Gauge("ey_invoice_fraud_score", "Latest fraud score by invoice", ["invoice_id"])
WORKFLOW_LATENCY = Histogram("ey_workflow_latency_seconds", "Workflow latency in seconds")
EXTRACTION_CONFIDENCE = Gauge("ey_extraction_confidence", "Extraction confidence by invoice", ["invoice_id"])


class TraceContext:
    def __init__(self, name: str, metadata: dict | None = None):
        self.name = name
        self.metadata = metadata or {}
        self.trace_id = str(uuid.uuid4())
        self.started_at = time.perf_counter()
        self.events: list[dict] = []

    def add_event(self, event_name: str, **kwargs):
        self.events.append({"event": event_name, "time": time.time(), **kwargs})

    def finish(self, status: str = "ok") -> dict:
        return {
            "trace_id": self.trace_id,
            "name": self.name,
            "status": status,
            "duration_ms": round((time.perf_counter() - self.started_at) * 1000, 2),
            "metadata": self.metadata,
            "events": self.events,
        }


@contextmanager
def workflow_timer():
    started = time.perf_counter()
    try:
        yield
    finally:
        WORKFLOW_LATENCY.observe(time.perf_counter() - started)


def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
