# Synthetic Data

This folder contains synthetic invoices, vendors, purchase orders, policy documents, and workflow definitions.

No real EY, vendor, client, employee, or procurement data is included.

## Files

- `purchase_orders.json`: PO master data for reconciliation.
- `vendors.json`: vendor risk metadata.
- `sample_structured_invoices.json`: historical invoices for fraud feature baselines.
- `sample_invoices/*.txt`: OCR-like invoice text inputs.
- `policies/*.md`: policy documents loaded into the RAG retriever.
- `workflows/invoice_compliance.yaml`: YAML state-machine definition.
