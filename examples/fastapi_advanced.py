"""
FastAPI integration example with advanced structured logging features.
"""

import asyncio
import time
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

from structured_logger import LoggerConfig, get_logger
from structured_logger.advanced import (
    CorrelationIDManager,
    LogSchema,
    MetricsConfig,
    SamplingConfig,
)

# Setup advanced logging configuration
schema = LogSchema(
    required_fields={"request_id", "method", "path"},
    field_types={"request_id": str, "method": str, "path": str},
)

sampling_config = SamplingConfig(
    sample_rate=1.0, burst_limit=100, max_logs_per_window=2000
)

metrics_config = MetricsConfig(
    enabled=True, track_performance=True, track_counts=True, metrics_interval=30
)

config = LoggerConfig(
    enable_async=True,  # Use async logging for FastAPI
    enable_validation=True,
    enable_sampling=True,
    enable_metrics=True,
    enable_correlation_ids=True,
    override_uvicorn_loggers=True,  # Enable structured logging for uvicorn
    log_schema=schema,
    sampling_config=sampling_config,
    metrics_config=metrics_config,
    force_json=True,
)

logger = get_logger(__name__, config=config)
app = FastAPI(title="Advanced Structured Logging Demo")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging with correlation IDs."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # Set correlation ID for this request
        CorrelationIDManager.set_correlation_id(request_id)

        await logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host,
            },
        )

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            await logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                },
            )

            return response

        except Exception as e:
            duration = time.time() - start_time

            await logger.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration * 1000, 2),
                    "exception_type": type(e).__name__,
                    "exception_message": str(e),
                },
                exc_info=True,
            )

            raise
        finally:
            # Clear correlation ID
            CorrelationIDManager.clear_correlation_id()


app.add_middleware(LoggingMiddleware)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with logging."""
    await logger.warning(
        "HTTP exception occurred",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
            "method": request.method,
        },
    )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.get("/")
async def root():
    """Root endpoint."""
    await logger.info("Root endpoint accessed")
    return {"message": "Hello World", "features": "Advanced Structured Logging"}


@app.get("/user/{user_id}")
async def get_user(user_id: str):
    """Get user endpoint with async logging."""
    await logger.info(
        "User lookup started", extra={"user_id": user_id, "operation": "get_user"}
    )

    # Simulate async database lookup
    await asyncio.sleep(0.1)

    await logger.info(
        "User lookup completed",
        extra={"user_id": user_id, "operation": "get_user", "found": True},
    )

    return {
        "user_id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com",
    }


@app.post("/user/{user_id}/action")
async def user_action(user_id: str, action: dict):
    """User action endpoint."""
    action_type = action.get("type", "unknown")

    await logger.info(
        "User action received",
        extra={
            "user_id": user_id,
            "action_type": action_type,
            "operation": "user_action",
        },
    )

    # Validate action
    if action_type not in ["login", "logout", "view", "edit"]:
        await logger.warning(
            "Invalid action type",
            extra={
                "user_id": user_id,
                "action_type": action_type,
                "valid_actions": ["login", "logout", "view", "edit"],
            },
        )
        raise HTTPException(status_code=400, detail="Invalid action type")

    # Process action
    await asyncio.sleep(0.05)

    await logger.info(
        "User action processed",
        extra={
            "user_id": user_id,
            "action_type": action_type,
            "operation": "user_action",
            "success": True,
        },
    )

    return {"status": "success", "action": action_type}


@app.get("/bulk/{count}")
async def bulk_operation(count: int):
    """Bulk operation for rate limiting demonstration."""
    if count > 100:
        raise HTTPException(status_code=400, detail="Count too large")

    await logger.info(
        "Bulk operation started", extra={"count": count, "operation": "bulk_operation"}
    )

    for i in range(count):
        await logger.info(
            f"Processing item {i+1}",
            extra={
                "item_number": i + 1,
                "total_items": count,
                "operation": "bulk_operation",
            },
        )
        await asyncio.sleep(0.01)  # Small delay

    await logger.info(
        "Bulk operation completed",
        extra={"count": count, "operation": "bulk_operation", "success": True},
    )

    return {"status": "completed", "processed": count}


@app.get("/error")
async def trigger_error():
    """Endpoint that triggers an error."""
    await logger.warning("Error endpoint accessed - this will fail")
    raise HTTPException(status_code=500, detail="Test error for logging demonstration")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    await logger.debug("Health check requested")
    return {"status": "healthy", "timestamp": time.time()}


if __name__ == "__main__":
    import uvicorn

    async def startup():
        await logger.info("FastAPI application starting with advanced logging")
        await logger.info("Uvicorn loggers are now using structured JSON formatting")

    app.add_event_handler("startup", startup)

    # Run with uvicorn - access logs and error logs will now be structured JSON
    # thanks to override_uvicorn_loggers=True in the config
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
