# Invoice Approval and Delegation of Authority Policy

## approval-thresholds
Invoices below INR 100,000 may be auto-approved when the purchase order is active, vendor identity matches, invoice total is within two percent of approved PO value, and document extraction confidence is above 0.85.

Invoices from INR 100,000 to INR 500,000 require AP Manager review when any exception is detected. If no exception is detected, automated approval is permitted but audit evidence must include PO match, line-item extraction, and vendor risk score.

Invoices above INR 500,000 require Finance Controller and Procurement Head approval. Enhanced audit sampling is required for high-value invoices, including duplicate-payment screening and policy-citation capture.

## document-quality
Invoices with extraction confidence below 0.85 must be routed to a document review analyst. Automated posting is not allowed when invoice date, vendor id, PO number, total amount, or tax amount cannot be extracted.

## inactive-po
Invoices linked to inactive purchase orders must not be posted automatically. They require AP Manager review and procurement confirmation.
