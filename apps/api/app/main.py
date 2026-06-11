"""FastAPI application factory and wiring.

Routers are registered incrementally as each implementation MD lands. The
application boots even if external providers are unconfigured; those endpoints
fail loudly with 424 at call time rather than at startup.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.config import settings
from app.logging_config import configure_logging
from app.metrics import PrometheusMiddleware, metrics_response
from app.middleware import CorrelationIdMiddleware
from app.routers import health

configure_logging(settings.log_level)
logger = logging.getLogger("truststack.startup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Best-effort: ensure the object-storage bucket exists. If storage is not
    # yet reachable the API still boots; /health will report the failure.
    try:
        from app.storage import ensure_bucket

        ensure_bucket()
    except Exception as exc:  # noqa: BLE001
        logger.warning("bucket_ensure_failed", extra={"fields": {"error": str(exc)}})
    logger.info(
        "api_startup",
        extra={"fields": {
            "environment": settings.app_env,
            "ocr_configured": settings.ocr_configured,
            "kyc_configured": settings.kyc_configured,
        }},
    )
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="TrustStack Lite API",
        version=__version__,
        description=(
            "Risk-adaptive onboarding, consent governance, document "
            "verification, and review operations."
        ),
        openapi_url="/openapi.json",
        docs_url="/docs",
        lifespan=lifespan,
    )

    app.add_middleware(PrometheusMiddleware)
    app.add_middleware(CorrelationIdMiddleware)

    app.include_router(health.router)

    # Routers added by later MDs (guarded so the app still boots if absent).
    _include_optional_routers(app)

    @app.get("/metrics", include_in_schema=False)
    def metrics():
        return metrics_response()

    return app


def _include_optional_routers(app: FastAPI) -> None:
    """Include feature routers added by MD 02+ without failing if not present yet."""
    optional = [
        ("app.routers.applicants", "router"),
        ("app.routers.cases", "router"),
        ("app.routers.audit", "router"),
        ("app.routers.auth", "router"),
        ("app.routers.api_keys", "router"),
        ("app.routers.notices", "router"),
        ("app.routers.consent", "router"),
        ("app.routers.retention", "router"),
        ("app.routers.documents", "router"),
        ("app.routers.verification", "router"),
        ("app.routers.risk", "router"),
        ("app.routers.webhooks", "router"),
    ]
    import importlib

    for module_path, attr in optional:
        try:
            module = importlib.import_module(module_path)
        except ModuleNotFoundError:
            continue
        router = getattr(module, attr, None)
        if router is not None:
            app.include_router(router)


app = create_app()
