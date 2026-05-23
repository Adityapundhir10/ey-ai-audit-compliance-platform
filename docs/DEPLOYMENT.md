# Deployment

## Local Docker

```bash
cp .env.example .env
docker compose up --build
```

## Render

Use `deploy/render.yaml`. Create a new Render blueprint from the GitHub repository. Add production secrets in Render's environment variable panel.

## Fly.io

```bash
fly launch --no-deploy
fly deploy
```

## Production checklist

- Use managed PostgreSQL instead of SQLite.
- Enable Redis/Celery or Kafka consumers for async processing.
- Store evidence bundles in object storage with retention policies.
- Use managed vector search for policy and SOP retrieval.
- Configure SSO and role-based access control.
- Configure OTLP exporter for traces.
- Add PII masking and secure secrets management.
- Run model evaluation on a labeled invoice dataset before claiming accuracy metrics.
