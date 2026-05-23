# Architecture

The platform is organized as a governed workflow automation system. Each stage is implemented as an independent agent with clear inputs, outputs, and auditable state transitions.

## Main components

1. **Document Intelligence**
   - OCR normalization cleans noisy invoice text.
   - Azure Form Recognizer adapter boundary is included for enterprise deployments.
   - Schema-constrained extraction validates required fields, dates, currency, and arithmetic consistency.

2. **PO Reconciliation**
   - Compares invoice vendor, PO ID, currency, approved amount, remaining balance, validity window, and line totals.
   - Emits severity-tagged reconciliation findings.

3. **Compliance RAG**
   - Loads finance control policies from `data/policies`.
   - Splits documents into sections.
   - Performs lexical + semantic-like hybrid retrieval and lightweight reranking.
   - Produces compliance findings with supporting evidence snippets.

4. **Fraud Intelligence**
   - Computes duplicate invoice risk.
   - Builds vendor rolling-window features.
   - Detects amount outliers and watchlist vendors.
   - Exposes a clean boundary for Isolation Forest, XGBoost, or managed ML model scoring.

5. **Approval Router**
   - Routes critical risks to audit partner review.
   - Routes high value or policy exceptions to finance controller review.
   - Auto-approves low-risk invoices.

6. **Audit Evidence**
   - Persists JSON and Markdown evidence bundles.
   - Captures risk score, policy context, findings, approval route, source document references, and workflow trace.

7. **Observability**
   - Prometheus counters/histograms/gauges.
   - Structured logs.
   - Trace events attached to each workflow run.

## Production extension points

- Replace local `HybridPolicyRetriever` with Weaviate, Azure AI Search, pgvector, or Elasticsearch.
- Replace regex extraction with Azure Document Intelligence custom invoice model.
- Replace deterministic fraud scoring with a trained Isolation Forest + XGBoost ensemble.
- Add Redis Queue/Celery/RQ for asynchronous execution.
- Add Kafka topics for document-submitted, invoice-extracted, risk-scored, and approval-routed events.
- Add LangGraph for persisted state-machine orchestration.
- Add LangSmith and LiteLLM for LLM traces, cost tracking, and hallucination evaluation.
