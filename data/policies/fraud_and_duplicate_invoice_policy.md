# Fraud and Duplicate Invoice Screening Policy

## duplicate-payment
Duplicate payment screening must compare invoice number, purchase order number, vendor id, total amount, tax amount, bank account metadata when available, and submission timing. A repeated PO and identical total amount must create an exception unless there is evidence of scheduled recurring billing.

## vendor-risk
High-risk vendors require additional review when invoices exceed historical averages by more than two standard deviations, when late submission rate exceeds fifteen percent, or when exception rate exceeds twenty percent.

## anomaly-detection
Anomaly detection may use rolling-window aggregation, lag features, vendor-level historical baselines, Isolation Forest, boosted-tree classifiers, or other approved models. The model decision must not be the sole basis for rejection; it must create a review recommendation with explainable risk signals.
