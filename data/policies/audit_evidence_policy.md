# Audit Evidence and AI Governance Policy

## evidence-retention
For each automated invoice decision, the system must retain structured extraction output, validation errors, PO reconciliation result, policy citations, fraud signals, approval routing, final decision, timestamp, workflow identifier, and trace identifier.

## human-in-the-loop
Human approval is required when policy thresholds are exceeded, fraud score is high, extraction confidence is low, or reconciliation fails. The approval event must preserve approver role, decision, conditions, and any supporting comments.

## ai-observability
AI services must expose workflow latency, document extraction confidence, fraud score, token utilization when external LLMs are used, retrieval confidence, citation count, and exception rates. Drift monitoring should compare current invoice distributions against historical baselines.
