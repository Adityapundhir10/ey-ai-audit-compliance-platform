# Observability

The project exposes workflow observability through three levels:

1. **Metrics**: Prometheus counters, gauges, and histograms from `/metrics`.
2. **Trace events**: Every workflow response includes a stage-by-stage `workflow_trace`.
3. **Logs**: Structured log messages for agent latency and workflow status.

Suggested dashboards:

- Workflow runs by status.
- Agent latency p50/p95.
- Risk score distribution.
- Approval route counts.
- Evidence generation failures.
- Token/cost usage if LiteLLM is connected.
- Retrieval quality and hallucination evaluation if LangSmith is connected.
