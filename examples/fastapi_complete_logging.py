"""
FastAPI example with complete structured logging setup.

This example shows how structured logging works automatically for:
1. Your application logs
2. Uvicorn server logs - ENABLED BY DEFAULT
3. Gunicorn server logs - ENABLED BY DEFAULT
4. Third-party library logs (httpx, sqlalchemy, etc.) - ENABLED BY DEFAULT

All logger overrides are now enabled by default! Just call get_logger() and everything works.
"""

from fastapi import FastAPI, Request
from structured_logger import LoggerConfig, get_logger

# All overrides are enabled by default! Just add custom fields if needed.
config = LoggerConfig(
    custom_fields=["request_id", "user_id"],
    include_extra_attrs=True,
    use_stdout_for_all=True,  # Railway/Docker compatible
    # These are all TRUE by default now:
    # override_uvicorn_loggers=True
    # override_gunicorn_loggers=True
    # override_library_loggers=True
)

# Get application logger - this automatically configures everything!
logger = get_logger(__name__, config=config)

app = FastAPI(title="Complete Logging Example")


@app.on_event("startup")
async def startup_event():
    """Log startup event."""
    logger.info("Application starting up")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests."""
    logger.info(
        "Incoming request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else None,
        },
    )
    response = await call_next(request)
    logger.info(
        "Request completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
        },
    )
    return response


@app.get("/")
async def root():
    """Root endpoint."""
    logger.info("Root endpoint called")
    return {"message": "Hello World"}


@app.get("/test-library-logs")
async def test_library_logs():
    """Test that library logs are formatted correctly."""
    import httpx
    import logging

    # This will use the structured formatter
    httpx_logger = logging.getLogger("httpx")
    httpx_logger.info("Testing httpx logger formatting")

    # This will also use the structured formatter
    sqlalchemy_logger = logging.getLogger("sqlalchemy")
    sqlalchemy_logger.info("Testing sqlalchemy logger formatting")

    logger.info("Library log test completed")
    return {"message": "Check logs for formatted output"}


@app.get("/test-error")
async def test_error():
    """Test error logging."""
    try:
        raise ValueError("This is a test error")
    except ValueError as e:
        logger.error("Error occurred", exc_info=True, extra={"error_type": "test"})
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn

    # All logs will now be structured JSON:
    # - Your application logs (logger.info, logger.error, etc.)
    # - Uvicorn logs (access logs, error logs)
    # - Third-party library logs (httpx, sqlalchemy, etc.)
    # - Any other logs from the root logger
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
