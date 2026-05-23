from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from .agents import MultiAgentInvoiceAuditGraph
from .config import settings
from .observability import metrics
from .storage import AuditRepository
from .task_queue import InMemoryWorkflowQueue

app = FastAPI(
    title=settings.app_name,
    description="AI enterprise audit and invoice compliance workflow API",
    version="0.1.0",
)

graph = MultiAgentInvoiceAuditGraph()
repo = AuditRepository(Path("./outputs/ey_audit_ai.db"))
workflow_queue = InMemoryWorkflowQueue()


class WorkflowRunRequest(BaseModel):
    invoice_document_text: str = Field(..., description="OCR text or extracted text from an invoice document")
    purchase_order: dict[str, Any]
    vendor_profile: dict[str, Any]
    historical_invoices: list[dict[str, Any]] = Field(default_factory=list)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "env": settings.app_env}


@app.get("/metrics")
def prometheus_metrics() -> Response:
    return Response(content=metrics.render_prometheus(), media_type="text/plain")


@app.post("/workflows/invoice-audit/run")
def run_invoice_audit(request: WorkflowRunRequest) -> dict[str, Any]:
    try:
        result = graph.run(request.model_dump())
        repo.save_run(
            invoice_id=result["invoice"]["invoice_id"],
            evidence_id=result["evidence_id"],
            risk_score=result["risk_score"],
            approval_route=result["approval"]["route"],
            payload=result,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/workflows/runs")
def list_runs(limit: int = 20) -> list[dict[str, Any]]:
    return repo.list_runs(limit=limit)


@app.get("/policies/search")
def search_policies(q: str, top_k: int = 5) -> dict[str, Any]:
    from .rag import PolicyChunker, HybridPolicyRetriever

    chunks = PolicyChunker().chunk_directory(settings.policy_docs_path)
    retriever = HybridPolicyRetriever(chunks)
    hits = retriever.retrieve(q, top_k=top_k)
    return {
        "query": q,
        "hits": [
            {
                "doc_id": hit.chunk.doc_id,
                "title": hit.chunk.title,
                "score": hit.score,
                "match_terms": hit.match_terms,
                "snippet": hit.chunk.text[:500],
            }
            for hit in hits
        ],
    }



def _run_background_task(task_id: str, payload: dict[str, Any]) -> None:
    workflow_queue.mark_running(task_id)
    try:
        result = graph.run(payload)
        repo.save_run(
            invoice_id=result["invoice"]["invoice_id"],
            evidence_id=result["evidence_id"],
            risk_score=result["risk_score"],
            approval_route=result["approval"]["route"],
            payload=result,
        )
        workflow_queue.mark_success(task_id, result)
    except Exception as exc:  # pragma: no cover
        workflow_queue.mark_failed(task_id, str(exc))


@app.post("/workflows/invoice-audit/submit")
def submit_invoice_audit(request: WorkflowRunRequest, background_tasks: BackgroundTasks) -> dict[str, Any]:
    """Submit workflow for asynchronous local execution."""
    task = workflow_queue.submit_sync(request.model_dump())
    background_tasks.add_task(_run_background_task, task.task_id, request.model_dump())
    return {"task_id": task.task_id, "state": task.state.value}


@app.get("/workflows/tasks/{task_id}")
def get_task(task_id: str) -> dict[str, Any]:
    try:
        return workflow_queue.serialize(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
