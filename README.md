# EY AI Enterprise Audit & Invoice Compliance Platform

A GitHub-ready reference implementation for an **AI-driven enterprise invoice validation and audit workflow system** inspired by an AI/ML engineering internship project at EY. The project demonstrates governed multi-agent workflow automation, invoice intelligence, PO reconciliation, fraud detection, RAG-based policy checks, audit evidence generation, and observability.

> This repository is designed as a portfolio project. It runs locally with synthetic demo data and adapter interfaces for enterprise services such as Azure Form Recognizer, LangGraph, LangSmith, LiteLLM, Prometheus, Grafana, PostgreSQL, Redis, and vector databases. It is deployment-ready through Docker and Render/Fly-style configs, but it is not already hosted on a public server.

## What this project shows

- Governed multi-agent workflow for invoice validation, PO reconciliation, approval escalation, and audit evidence generation.
- Document intelligence pipeline with OCR normalization, schema-constrained extraction, and strict validation.
- Compliance intelligence using hybrid RAG retrieval over finance policies and vendor SOPs.
- Fraud and anomaly detection using duplicate-invoice checks, rolling-window vendor features, robust scoring, and optional ML adapters.
- Observability with structured logs, Prometheus metrics, OpenTelemetry-style spans, cost/latency tracking hooks, and LiteLLM/LangSmith adapter boundaries.
- Production-style code layout, tests, Docker, CI, deployment configs, sample data, and architecture diagrams.

## Architecture

![Architecture](assets/architecture.svg)

```text
Invoice docs -> Document Intelligence -> Validation -> PO Reconciliation
      -> RAG Compliance Agent -> Fraud Agent -> Approval Router -> Audit Evidence
      -> Observability: metrics, traces, logs, token/cost stats
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m ey_audit_ai.cli run-demo
```

Run the API:

```bash
uvicorn ey_audit_ai.main:app --reload --host 0.0.0.0 --port 8000
```

Open:

- API docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`
- Metrics: `http://localhost:8000/metrics`

## Docker

```bash
docker compose up --build
```

The app starts at `http://localhost:8000`. Prometheus is configured at `http://localhost:9090`; Grafana is included as a profile/service example in `docker-compose.yml`.

## Example API request

```bash
curl -X POST http://localhost:8000/workflows/invoice-audit/run \
  -H "Content-Type: application/json" \
  -d @data/demo_payloads/invoice_workflow_request.json

# async local submission
curl -X POST http://localhost:8000/workflows/invoice-audit/submit \
  -H "Content-Type: application/json" \
  -d @data/demo_payloads/invoice_workflow_request.json
```

## Repository structure

```text
ey-ai-enterprise-audit-invoice-compliance/
├── src/ey_audit_ai/
│   ├── main.py                       # FastAPI app
│   ├── agents.py                     # Multi-agent compliance workflow
│   ├── workflow_engine.py            # YAML-driven state machine runner
│   ├── document_intelligence.py      # OCR normalization and extraction
│   ├── reconciliation.py             # PO/invoice matching logic
│   ├── fraud.py                      # Duplicate and anomaly intelligence
│   ├── rag.py                        # Hybrid retrieval and reranking
│   ├── audit_evidence.py             # Evidence bundle generation
│   ├── observability.py              # Metrics/traces/logging hooks
│   ├── storage.py                    # SQLite persistence adapter
│   └── cli.py                        # Demo runner
├── data/                             # Synthetic invoices, POs, policies
├── workflows/                        # YAML workflow definitions
├── assets/                           # Architecture diagrams
├── docs/                             # Architecture, API, deployment docs
├── monitoring/                       # Prometheus/Grafana configs
├── tests/                            # Unit/integration tests
└── deploy/                           # Render/Fly deployment examples
```

## Demo output

The CLI demo reads synthetic invoice and purchase order data, executes the agent graph, and writes an audit evidence bundle to `outputs/evidence/`.

```bash
python -m ey_audit_ai.cli run-demo --output outputs/evidence
```

## Environment variables

Copy `.env.example` to `.env` and update values as needed.

```bash
cp .env.example .env
```

Core local mode does not require cloud credentials. Azure/OpenAI/LangSmith keys are optional and are only used by adapters if you enable them.

## Resume alignment

See [`docs/RESUME_MAPPING.md`](docs/RESUME_MAPPING.md) for a line-by-line explanation of how this repository maps to the resume bullets.

## Important honesty note

The project includes realistic synthetic data and integration adapters, but reported metrics such as 97% extraction accuracy or ROC-AUC 0.93 should only be claimed if you reproduce them on a real labeled dataset. This demo contains a benchmark harness and synthetic examples so you can extend it responsibly.
