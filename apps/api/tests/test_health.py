"""Health endpoint tests.

Run inside the api container (`docker compose exec api pytest`) where the real
database, Redis, and MinIO are reachable. There is no mocked dependency: if a
backing service is down these assertions fail, which is the intended behaviour.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_liveness_does_not_touch_dependencies():
    resp = client.get("/health/live")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_health_reports_core_services_and_providers():
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["checks"]["database"]["status"] == "ok"
    assert body["checks"]["redis"]["status"] == "ok"
    assert body["checks"]["object_storage"]["status"] == "ok"
    # External providers must be REPORTED (configured/not_configured), never hidden.
    # The exact value depends on whether OCR/KYC credentials are present in env.
    assert body["providers"]["ocr"] in {"configured", "not_configured"}
    assert body["providers"]["kyc"] in {"configured", "not_configured"}


def test_metrics_exposed():
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "truststack_http_requests_total" in resp.text
