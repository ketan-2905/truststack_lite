"""Health endpoint.

Validates the real backing services (database, Redis, object storage) and
reports the configuration state of external providers (OCR, KYC). Missing
external credentials are reported as ``not_configured`` rather than hidden, in
line with the project's no-fake-success rule.
"""

from __future__ import annotations

from fastapi import APIRouter, Response

from app import __version__
from app.config import settings
from app.db import check_database
from app.redis_client import check_redis
from app.storage import check_storage

router = APIRouter(tags=["health"])


def _probe(fn) -> dict:
    try:
        fn()
        return {"status": "ok"}
    except Exception as exc:  # noqa: BLE001 - surface the real failure reason
        return {"status": "error", "detail": str(exc)}


@router.get("/health")
def health(response: Response) -> dict:
    checks = {
        "database": _probe(check_database),
        "redis": _probe(check_redis),
        "object_storage": _probe(check_storage),
    }
    providers = {
        "ocr": "configured" if settings.ocr_configured else "not_configured",
        "kyc": "configured" if settings.kyc_configured else "not_configured",
    }

    core_ok = all(c["status"] == "ok" for c in checks.values())
    if not core_ok:
        response.status_code = 503

    return {
        "status": "ok" if core_ok else "error",
        "service": settings.service_name,
        "version": __version__,
        "environment": settings.app_env,
        "checks": checks,
        "providers": providers,
    }


@router.get("/health/live")
def liveness() -> dict:
    """Liveness probe: process is up. Does not touch dependencies."""
    return {"status": "ok"}


@router.get("/health/ready")
def readiness(response: Response) -> dict:
    """Readiness probe: dependencies are reachable."""
    return health(response)
