"""Prometheus metrics exposition.

A lightweight request counter/histogram so the Prometheus service configured in
docker-compose has a live target. Full tracing/metrics is expanded in MD 10.
"""

from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUEST_COUNT = Counter(
    "truststack_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "truststack_http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path"],
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Use the route template (not the raw path) to avoid label cardinality blowups.
        with REQUEST_LATENCY.labels(request.method, request.url.path).time():
            response = await call_next(request)
        REQUEST_COUNT.labels(
            request.method, request.url.path, str(response.status_code)
        ).inc()
        return response


def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
