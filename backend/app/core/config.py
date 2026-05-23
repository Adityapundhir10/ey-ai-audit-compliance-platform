from functools import lru_cache
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def default_project_root() -> Path:
    here = Path(__file__).resolve()
    candidates = [here.parents[2], here.parents[3] if len(here.parents) > 3 else here.parents[2]]
    for candidate in candidates:
        if (candidate / "data").exists():
            return candidate
        if (candidate.parent / "data").exists():
            return candidate.parent
    return here.parents[2]


class Settings(BaseSettings):
    app_name: str = "EY-Style AI Enterprise Audit Platform"
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"
    secret_key: str = "change-me"

    database_url: str = "sqlite:///./ey_audit_demo.db"
    redis_url: str = "redis://localhost:6379/0"
    kafka_bootstrap_servers: str = "localhost:9092"
    weaviate_url: str = "http://localhost:8080"

    azure_form_recognizer_endpoint: Optional[str] = None
    azure_form_recognizer_key: Optional[str] = None
    azure_form_recognizer_model_id: str = "prebuilt-invoice"

    llm_provider: str = "local"
    openai_api_key: Optional[str] = None
    litellm_base_url: Optional[str] = None
    litellm_model: str = "gpt-4o-mini"

    enable_weaviate: bool = False
    enable_kafka: bool = False
    enable_langsmith: bool = False
    prometheus_enabled: bool = True
    otel_enabled: bool = True

    project_root: Path = Field(default_factory=default_project_root)
    data_dir: Path = Field(default_factory=lambda: default_project_root() / "data")
    artifacts_dir: Path = Field(default_factory=lambda: default_project_root() / "artifacts")

    model_config = SettingsConfigDict(env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.artifacts_dir.mkdir(parents=True, exist_ok=True)
    return settings
