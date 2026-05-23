# Model Card and Responsible AI Notes

## Purpose

This repository demonstrates invoice extraction, compliance routing, and fraud-risk scoring. It is not a production fraud adjudication system.

## Data

All sample data is synthetic. No real client, EY, vendor, employee, invoice, or purchase order data is included.

## Models

- OCR normalization: deterministic text cleanup.
- Extraction: regex and schema validation fallback; Azure Document Intelligence adapter placeholder.
- Retrieval: local hybrid lexical retrieval; optional Weaviate replacement.
- Fraud: rules plus Isolation Forest anomaly component.

## Limitations

- Fraud scores are risk prioritization signals, not final decisions.
- Human review is required for high-risk or high-value decisions.
- Extraction accuracy claims in README are simulated portfolio KPIs and should be validated on real labeled data before production use.

## Governance Controls

- Audit packet generation.
- Trace ID on each workflow.
- Policy citation capture.
- Explainable fraud signals.
- Metrics endpoint for drift and latency monitoring.
