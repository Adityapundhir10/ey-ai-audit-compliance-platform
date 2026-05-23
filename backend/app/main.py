from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
except Exception:  # optional dependency in lightweight local mode
    FastAPIInstrumentor = None
from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import init_db
from app.observability import metrics_response

settings = get_settings()
configure_logging()
init_db()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Clean-room EY-style AI invoice compliance, audit workflow, RAG, fraud detection, and observability platform.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.api_prefix)


@app.get("/")
def root() -> dict:
    return {
        "service": settings.app_name,
        "docs": "/docs",
        "health": f"{settings.api_prefix}/health",
        "metrics": "/metrics",
    }


@app.get("/metrics")
def metrics():
    return metrics_response()


if settings.otel_enabled and FastAPIInstrumentor is not None:
    FastAPIInstrumentor.instrument_app(app)
