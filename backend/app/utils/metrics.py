"""Prometheus metrics configuration."""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
from functools import wraps
import time

# Create registry
registry = CollectorRegistry()

# Metrics
workflow_executions = Counter(
    "faa_workflow_executions_total",
    "Total number of workflow executions",
    ["status"],
    registry=registry,
)

workflow_duration = Histogram(
    "faa_workflow_duration_seconds",
    "Workflow execution duration",
    ["status"],
    registry=registry,
)

workflow_retries = Counter(
    "faa_workflow_retries_total",
    "Total number of workflow retries",
    registry=registry,
)

evaluation_scores = Histogram(
    "faa_evaluation_scores",
    "Evaluation scores distribution",
    ["metric"],
    buckets=[1, 2, 3, 4, 5],
    registry=registry,
)

active_conversations = Gauge(
    "faa_active_conversations",
    "Number of active conversations",
    registry=registry,
)

llm_calls = Counter(
    "faa_llm_calls_total",
    "Total LLM API calls",
    ["provider", "model"],
    registry=registry,
)

llm_tokens = Counter(
    "faa_llm_tokens_total",
    "Total tokens used",
    ["provider", "model", "type"],
    registry=registry,
)


def track_workflow_execution(func):
    """Decorator to track workflow execution metrics."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        status = "success"

        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            status = "error"
            raise
        finally:
            duration = time.time() - start_time
            workflow_executions.labels(status=status).inc()
            workflow_duration.labels(status=status).observe(duration)

    return wrapper


def setup_metrics() -> None:
    """Initialize metrics collection."""
    # Any additional setup needed
    pass
