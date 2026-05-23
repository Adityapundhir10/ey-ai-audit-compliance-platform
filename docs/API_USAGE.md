# API Usage

Start the backend and open `/docs` for interactive OpenAPI.

## Reset demo data

```bash
curl -X POST http://localhost:8000/api/v1/demo/reset
```

## Run workflow

```bash
curl -X POST http://localhost:8000/api/v1/workflows/run \
  -H "Content-Type: application/json" \
  -d @data/demo_payloads/workflow_invoice_1001.json
```

## Extract document only

```bash
curl -X POST http://localhost:8000/api/v1/documents/extract \
  -H "Content-Type: application/json" \
  -d '{"raw_text":"Invoice Number: INV-1 ..."}'
```

## Ask RAG policy engine

```bash
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What approval is required above INR 500000?","top_k":3}'
```

## Get audit packet

```bash
curl http://localhost:8000/api/v1/audit/evidence/INV-1001
```
