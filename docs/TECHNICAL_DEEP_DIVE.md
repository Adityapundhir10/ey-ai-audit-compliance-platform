# Technical Deep Dive

## Workflow State

Each workflow has a unique `WF-*` identifier. The platform persists state after each agent node, which enables recovery, traceability, and future retry semantics.

## Multi-Agent Design

The agents are intentionally decoupled:

- Intake checks payload completeness and priority.
- Extraction transforms raw text into validated financial objects.
- Reconciliation compares PO and invoice fields.
- Compliance applies deterministic controls and retrieves policy citations.
- Fraud scores duplicate, outlier, and vendor-risk behavior.
- Human Approval simulates an enterprise review queue.
- Audit Evidence creates immutable review-ready evidence packets.

## RAG Implementation

The local implementation uses hybrid lexical scoring so the project can run on any machine. The interface is built so it can be replaced by Weaviate, Azure AI Search, OpenSearch, pgvector, or Pinecone.

## Fraud Features

The score combines:

- Duplicate count for same PO and amount.
- Historical vendor average deviation.
- Vendor risk tier.
- Extraction uncertainty.
- High-value invoice flag.
- Isolation Forest anomaly component when enough historical data exists.

## Observability

Metrics are exposed through Prometheus:

- `ey_workflow_runs_total`
- `ey_agent_invocations_total`
- `ey_llm_calls_total`
- `ey_invoice_fraud_score`
- `ey_workflow_latency_seconds`
- `ey_extraction_confidence`

## Extension Points

- Replace local extraction with Azure Form Recognizer.
- Replace local RAG with Weaviate dense vectors.
- Publish state events to Redpanda/Kafka.
- Add SSO and RBAC.
- Add real model registry and evaluation artifacts.
- Add immutable audit evidence storage.
