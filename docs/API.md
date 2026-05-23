# API Guide

## Health

`GET /health`

Returns service status.

## Run invoice audit workflow

`POST /workflows/invoice-audit/run`

Request body:

```json
{
  "invoice_document_text": "INVOICE...",
  "purchase_order": {
    "po_id": "PO-2025-7781",
    "vendor_id": "VND-8842",
    "currency": "INR",
    "approved_total": 31000,
    "remaining_balance": 32000,
    "valid_from": "2025-06-01",
    "valid_to": "2025-09-30",
    "cost_center": "CC-FAC-009",
    "approver_email": "finance.controller@example.com",
    "status": "approved",
    "line_items": []
  },
  "vendor_profile": {
    "vendor_id": "VND-8842",
    "vendor_name": "Northstar Facilities Pvt Ltd",
    "risk_tier": "medium",
    "country": "IN",
    "average_invoice_value": 14500,
    "on_watchlist": false
  },
  "historical_invoices": []
}
```

Response includes extracted invoice fields, reconciliation results, fraud signals, compliance findings, approval route, evidence ID, and workflow trace.

## Search policies

`GET /policies/search?q=duplicate%20invoice&top_k=5`

Returns RAG retrieval hits from local policy files.

## Metrics

`GET /metrics`

Prometheus-compatible metrics endpoint.
