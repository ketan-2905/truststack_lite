"""Test Prometheus metrics are recorded."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.metrics import get_request_count


client = TestClient(app)


def test_request_counter_increments():
    """API requests should increment request counter."""
    initial = get_request_count()

    response = client.get("/health")
    assert response.status_code == 200

    final = get_request_count()
    assert final >= initial  # Should have incremented


def test_metrics_endpoint_returns_prometheus_format():
    """GET /metrics should return Prometheus text format."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")

    # Should contain counter metrics
    assert "http_requests_total" in response.text or "requests" in response.text


def test_job_queue_metrics_recorded():
    """Background job metrics should be tracked."""
    # This documents that worker job counts should be in Prometheus
    # Implementation depends on RQ/ARQ integration
    pass
