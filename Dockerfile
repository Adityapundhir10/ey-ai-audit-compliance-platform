FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt pyproject.toml README.md ./
COPY src ./src
COPY data ./data
COPY workflows ./workflows
COPY monitoring ./monitoring

RUN pip install -r requirements.txt && pip install -e .

EXPOSE 8000

CMD ["uvicorn", "ey_audit_ai.main:app", "--host", "0.0.0.0", "--port", "8000"]
