from prometheus_client import Counter, Histogram, Gauge
from typing import Optional


# Metrics for model inference
MODEL_INFERENCE_LATENCY = Histogram(
    'model_inference_latency_seconds',
    'Time spent on model inference',
    ['model_version']
)

MODEL_PREDICTION_REQUESTS = Counter(
    'model_prediction_requests_total',
    'Total number of prediction requests',
    ['model_version', 'status']
)

MODEL_PREDICTION_ERRORS = Counter(
    'model_prediction_errors_total',
    'Total number of prediction errors',
    ['model_version', 'error_type']
)

MODEL_VERSION_ACTIVE = Gauge(
    'model_version_active',
    'Currently active model version',
    ['version']
)

MODEL_LOAD_TIME = Histogram(
    'model_load_time_seconds',
    'Time spent loading models',
    ['model_version']
)


def record_inference_latency(version: str, duration: float):
    """Record inference latency for a model version."""
    MODEL_INFERENCE_LATENCY.labels(model_version=version).observe(duration)


def record_prediction_request(version: str, status: str = "success"):
    """Record a prediction request."""
    MODEL_PREDICTION_REQUESTS.labels(model_version=version, status=status).inc()


def record_prediction_error(version: str, error_type: str):
    """Record a prediction error."""
    MODEL_PREDICTION_ERRORS.labels(model_version=version, error_type=error_type).inc()


def set_active_version(version: str):
    """Set the currently active model version."""
    # Reset all versions to 0
    for v in ["v1", "v2", "v3", "v4", "v5"]:  # Common version names
        MODEL_VERSION_ACTIVE.labels(version=v).set(0)
    
    # Set the active version to 1
    MODEL_VERSION_ACTIVE.labels(version=version).set(1)


def record_model_load_time(version: str, duration: float):
    """Record model loading time."""
    MODEL_LOAD_TIME.labels(model_version=version).observe(duration) 