#!/usr/bin/env bash
set -euo pipefail
curl -X POST http://localhost:8000/workflows/invoice-audit/run \
  -H "Content-Type: application/json" \
  -d @data/demo_payloads/invoice_workflow_request.json
