from fastapi import APIRouter, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    CONTENT_TYPE_LATEST,
    generate_latest,
)

router = APIRouter()

http_requests_total = Counter(
    "app_http_requests_total",
    "Count of HTTP requests received by the backend",
    ["method", "path", "status"],
)
job_creations_total = Counter(
    "app_job_creations_total",
    "Number of jobs created through the API",
)
job_triggers_total = Counter(
    "app_job_triggers_total",
    "Number of manual job trigger requests",
)
job_executions_total = Counter(
    "app_job_executions_total",
    "Number of job execution records created",
)
execution_duration_seconds = Histogram(
    "app_execution_duration_seconds",
    "Duration of job executions in seconds",
)
estimated_usage = Gauge(
    "project_estimated_usage",
    "Estimated usage values for different tiers and categories",
    ["tier", "category"],
)

_ESTIMATED_USAGE = {
    ("small_team", "registered_users"): 20,
    ("small_team", "daily_api_requests"): 100,
    ("small_team", "active_jobs"): 40,
    ("small_team", "daily_job_executions"): 200,
    ("small_team", "peak_tps"): 0.3,
    ("small_team", "avg_job_definition_size_bytes"): 1024,
    ("small_team", "avg_execution_log_size_bytes"): 5 * 1024,
    ("small_team", "storage_growth_bytes_per_month"): 30 * 1024 * 1024,
    ("small_team", "workflow_executions"): 0,
    ("mid_company", "registered_users"): 200,
    ("mid_company", "daily_api_requests"): 1000,
    ("mid_company", "active_jobs"): 1000,
    ("mid_company", "daily_job_executions"): 5000,
    ("mid_company", "peak_tps"): 8.3,
    ("mid_company", "avg_job_definition_size_bytes"): 5 * 1024,
    ("mid_company", "avg_execution_log_size_bytes"): 20 * 1024,
    ("mid_company", "storage_growth_bytes_per_month"): 3.75 * 1024 * 1024 * 1024,
    ("mid_company", "workflow_executions"): 90000,
    ("enterprise", "registered_users"): 2000,
    ("enterprise", "daily_api_requests"): 10000,
    ("enterprise", "active_jobs"): 20000,
    ("enterprise", "daily_job_executions"): 100000,
    ("enterprise", "peak_tps"): 166.7,
    ("enterprise", "avg_job_definition_size_bytes"): 5 * 1024,
    ("enterprise", "avg_execution_log_size_bytes"): 50 * 1024,
    ("enterprise", "storage_growth_bytes_per_month"): 165 * 1024 * 1024 * 1024,
    ("enterprise", "workflow_executions"): 3000000,
}

for (tier, category), value in _ESTIMATED_USAGE.items():
    estimated_usage.labels(tier=tier, category=category).set(value)


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        http_requests_total.labels(
            method=request.method,
            path=request.url.path,
            status=str(response.status_code),
        ).inc()
        return response


@router.get("/metrics")
async def metrics_endpoint() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
