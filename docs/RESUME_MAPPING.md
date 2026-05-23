# Resume Bullet Mapping

This repository maps to the EY project bullets as follows.

## Governed multi-agent workflow

Implemented in `src/ey_audit_ai/agents.py` with clear agents for extraction, reconciliation, compliance RAG, fraud detection, approval routing, and evidence generation. `workflows/invoice_compliance.yaml` shows how the same stages can be represented as a YAML-driven workflow.

## Document intelligence

Implemented in `src/ey_audit_ai/document_intelligence.py`. The code includes OCR normalization, adapter boundaries for Azure Form Recognizer, regex-based local extraction, strict schema validation, and arithmetic consistency checks.

## Fraud detection and compliance intelligence

Implemented in `src/ey_audit_ai/fraud.py` and `src/ey_audit_ai/rag.py`. The demo includes duplicate invoice detection, vendor rolling-window aggregation, watchlist controls, outlier scoring, hybrid policy retrieval, and reranking.

## Observability

Implemented in `src/ey_audit_ai/observability.py`, `monitoring/prometheus.yml`, and Grafana provisioning files. The API exposes `/metrics`, and each workflow response includes a detailed trace.

## Deployment and GitHub readiness

Docker, docker-compose, Render, Fly, GitHub Actions, Postman collection, docs, and sample data are included.

## Responsible metric note

The repository supports the architecture described in the resume, but numerical claims such as 97% extraction accuracy, F1 0.95, ROC-AUC 0.93, or 29% cost reduction should be presented as results only if you benchmark them using a real labeled dataset.
