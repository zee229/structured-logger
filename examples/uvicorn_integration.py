"""
Example demonstrating uvicorn logger integration with structured logging.

This example shows how to configure uvicorn loggers to use structured JSON formatting,
making it easier to parse and analyze uvicorn access logs and error logs in production.
"""

import asyncio
import time
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.base import BaseHTTPMiddleware

from structured_logger import LoggerConfig, get_logger, setup_uvicorn_logging

# Method 1: Using setup_uvicorn_logging convenience function
# This is the simplest way to enable structured logging for uvicorn
setup_uvicorn_logging(force_json=True)

# Method 2: Using LoggerConfig with uvicorn override enabled
config = LoggerConfig(
    override_uvicorn_loggers=True,  # Enable uvicorn logger override
    custom_fields=["request_id", "user_id", "trace_id"],
    include_extra_attrs=True,
)

# Get our application logger
logger = get_logger(__name__, config=config, force_json=True)

app = FastAPI(title="Uvicorn Structured Logging Demo")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to add request context to logs."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # Add request context to all logs in this request
        request.state.request_id = request_id

        # Log the incoming request
        await logger.info(
            "Incoming request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
            },
        )

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Log the response
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


app.add_middleware(RequestLoggingMiddleware)


@app.get("/")
async def root():
    """Root endpoint."""
    await logger.info("Root endpoint accessed")
    return {
        "message": "Hello World",
        "features": "Uvicorn Structured Logging",
        "note": "Check the console logs - uvicorn logs are now structured JSON!",
    }


@app.get("/user/{user_id}")
async def get_user(user_id: str, request: Request):
    """Get user endpoint with structured logging."""
    request_id = getattr(request.state, "request_id", "unknown")

    await logger.info(
        "User lookup started",
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "operation": "get_user",
        },
    )

    # Simulate database lookup
    await asyncio.sleep(0.1)

    user_data = {
        "user_id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com",
    }

    await logger.info(
        "User lookup completed",
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "operation": "get_user",
            "found": True,
        },
    )

    return user_data


@app.post("/user/{user_id}/action")
async def user_action(user_id: str, action: dict, request: Request):
    """User action endpoint."""
    request_id = getattr(request.state, "request_id", "unknown")
    action_type = action.get("type", "unknown")

    await logger.info(
        "User action received",
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "action_type": action_type,
            "operation": "user_action",
        },
    )

    # Validate action
    valid_actions = ["login", "logout", "view", "edit"]
    if action_type not in valid_actions:
        await logger.warning(
            "Invalid action type",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "action_type": action_type,
                "valid_actions": valid_actions,
            },
        )
        raise HTTPException(status_code=400, detail="Invalid action type")

    # Process action
    await asyncio.sleep(0.05)

    await logger.info(
        "User action processed",
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "action_type": action_type,
            "operation": "user_action",
            "success": True,
        },
    )

    return {"status": "success", "action": action_type}


@app.get("/error")
async def trigger_error():
    """Endpoint that triggers an error to demonstrate error logging."""
    await logger.warning("Error endpoint accessed - this will fail")
    raise HTTPException(status_code=500, detail="Test error for logging demonstration")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    await logger.debug("Health check requested")
    return {"status": "healthy", "timestamp": time.time()}


@app.get("/logs/test")
async def test_logs():
    """Endpoint to test different log levels."""
    await logger.debug("Debug message from application")
    await logger.info("Info message from application")
    await logger.warning("Warning message from application")
    await logger.error("Error message from application")

    return {
        "message": "Log messages sent",
        "note": "Check console for structured logs from both application and uvicorn",
    }


if __name__ == "__main__":
    import uvicorn

    async def startup():
        await logger.info(
            "FastAPI application starting with uvicorn structured logging enabled"
        )

    app.add_event_handler("startup", startup)

    # Run with uvicorn
    # The uvicorn logs (access logs, error logs) will now be structured JSON
    # because we enabled override_uvicorn_loggers
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        # Note: uvicorn's built-in access logging will be overridden
        # by our structured formatter
    )
