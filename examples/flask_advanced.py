"""
Flask integration example with advanced structured logging features.
"""

import time
import uuid

from flask import Flask, g, request

from structured_logger import LoggerConfig, get_logger
from structured_logger.advanced import (CorrelationIDManager, LogSchema,
                                        MetricsConfig, SamplingConfig)

app = Flask(__name__)

# Setup advanced logging configuration
schema = LogSchema(
    required_fields={"request_id", "method", "path"},
    field_types={"request_id": str, "method": str, "path": str},
    field_validators={
        "method": lambda x: x in ["GET", "POST", "PUT", "DELETE", "PATCH"],
        "path": lambda x: len(x) > 0,
    },
)

sampling_config = SamplingConfig(
    sample_rate=1.0,  # Log all requests in this example
    burst_limit=50,
    max_logs_per_window=1000,
)

metrics_config = MetricsConfig(
    enabled=True, track_performance=True, track_counts=True, metrics_interval=30
)

config = LoggerConfig(
    enable_validation=True,
    enable_sampling=True,
    enable_metrics=True,
    enable_correlation_ids=True,
    log_schema=schema,
    sampling_config=sampling_config,
    metrics_config=metrics_config,
    force_json=True,
)

logger = get_logger(__name__, config=config)


@app.before_request
def before_request():
    """Setup request context and correlation ID."""
    g.request_id = str(uuid.uuid4())
    g.start_time = time.time()

    # Set correlation ID for this request
    CorrelationIDManager.set_correlation_id(g.request_id)

    logger.info(
        "Request started",
        extra={
            "request_id": g.request_id,
            "method": request.method,
            "path": request.path,
            "user_agent": request.headers.get("User-Agent", ""),
            "remote_addr": request.remote_addr,
        },
    )


@app.after_request
def after_request(response):
    """Log request completion with metrics."""
    duration = time.time() - g.start_time

    logger.info(
        "Request completed",
        extra={
            "request_id": g.request_id,
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "response_size": len(response.get_data()),
        },
    )

    # Clear correlation ID
    CorrelationIDManager.clear_correlation_id()

    return response


@app.errorhandler(Exception)
def handle_exception(e):
    """Handle and log exceptions."""
    logger.error(
        "Unhandled exception",
        extra={
            "request_id": getattr(g, "request_id", None),
            "method": request.method,
            "path": request.path,
            "exception_type": type(e).__name__,
            "exception_message": str(e),
        },
        exc_info=True,
    )
    return {"error": "Internal server error"}, 500


@app.route("/")
def hello():
    """Simple hello endpoint."""
    logger.info("Hello endpoint accessed")
    return {"message": "Hello, World!", "request_id": g.request_id}


@app.route("/user/<user_id>")
def get_user(user_id):
    """User endpoint with validation."""
    logger.info(
        "User data requested",
        extra={"request_id": g.request_id, "user_id": user_id, "operation": "get_user"},
    )

    # Simulate some processing
    time.sleep(0.1)

    return {"user_id": user_id, "name": f"User {user_id}", "request_id": g.request_id}


@app.route("/error")
def trigger_error():
    """Endpoint that triggers an error for testing."""
    logger.warning("Error endpoint accessed - this will fail")
    raise ValueError("Test error for logging demonstration")


@app.route("/bulk")
def bulk_operation():
    """Endpoint that generates many logs for rate limiting demo."""
    for i in range(20):
        logger.info(
            f"Bulk operation step {i}",
            extra={"request_id": g.request_id, "step": i, "operation": "bulk_process"},
        )

    return {"message": "Bulk operation completed", "request_id": g.request_id}


if __name__ == "__main__":
    logger.info("Flask application starting with advanced logging")
    app.run(debug=True, port=5000)
