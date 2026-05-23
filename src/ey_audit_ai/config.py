from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "EY AI Enterprise Audit & Invoice Compliance Platform")
    app_env: str = os.getenv("APP_ENV", "local")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./outputs/ey_audit_ai.db")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    vector_index_path: Path = Path(os.getenv("VECTOR_INDEX_PATH", "./outputs/vector_index.json"))
    policy_docs_path: Path = Path(os.getenv("POLICY_DOCS_PATH", "./data/policies"))
    evidence_output_dir: Path = Path(os.getenv("EVIDENCE_OUTPUT_DIR", "./outputs/evidence"))
    enable_azure_form_recognizer: bool = _bool(os.getenv("ENABLE_AZURE_FORM_RECOGNIZER"), False)
    azure_form_recognizer_endpoint: str = os.getenv("AZURE_FORM_RECOGNIZER_ENDPOINT", "")
    azure_form_recognizer_key: str = os.getenv("AZURE_FORM_RECOGNIZER_KEY", "")
    enable_openai_llm: bool = _bool(os.getenv("ENABLE_OPENAI_LLM"), False)
    risk_approval_threshold: float = float(os.getenv("RISK_APPROVAL_THRESHOLD", "0.70"))
    high_value_invoice_threshold: float = float(os.getenv("HIGH_VALUE_INVOICE_THRESHOLD", "25000"))
    amount_tolerance_percent: float = float(os.getenv("AMOUNT_TOLERANCE_PERCENT", "2.0"))


settings = Settings()
