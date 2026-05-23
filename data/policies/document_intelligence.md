# Document Intelligence Standard

## Extraction Quality
Invoice extraction systems must capture vendor ID, invoice ID, PO ID, invoice date, due date, currency, line items, subtotal, tax, total, and payment terms.

## OCR Normalization
OCR output must be normalized for common invoice artifacts such as character confusion, spacing issues, repeated headers, and currency symbols before structured extraction.

## Schema-Constrained Extraction
All AI extraction outputs must be validated against a strict schema and checked for arithmetic consistency between subtotal, tax, and total.
