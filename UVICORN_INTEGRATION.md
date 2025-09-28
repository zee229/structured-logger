# Uvicorn Integration Guide

The structured-logger package now includes built-in support for formatting uvicorn logs as structured JSON. This is particularly useful for FastAPI applications where you want consistent log formatting across both your application logs and the web server logs.

## Overview

When you enable uvicorn integration, the following loggers are automatically configured to use structured JSON formatting:

- `uvicorn` - Main uvicorn logger
- `uvicorn.access` - HTTP access logs (requests/responses)
- `uvicorn.error` - Error logs
- `uvicorn.asgi` - ASGI-related logs

## Quick Start

### Method 1: Simple Setup (Recommended)

```python
from structured_logger import setup_uvicorn_logging

# This will override all uvicorn loggers with structured formatting
setup_uvicorn_logging(force_json=True)
```

### Method 2: Configuration-Based Setup

```python
from structured_logger import LoggerConfig, get_logger

config = LoggerConfig(
    override_uvicorn_loggers=True,  # Enable uvicorn override
    custom_fields=["request_id", "user_id", "trace_id"],
    include_extra_attrs=True,
)

logger = get_logger(__name__, config=config)
```

## FastAPI Integration Example

```python
from fastapi import FastAPI, Request
from structured_logger import setup_uvicorn_logging, get_logger
import uuid
import time

# Setup uvicorn logging first
setup_uvicorn_logging(force_json=True)

app = FastAPI()
logger = get_logger(__name__, force_json=True)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Your application logs
    await logger.info(
        "Request started",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
        }
    )
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    await logger.info(
        "Request completed",
        extra={
            "request_id": request_id,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
        }
    )
    
    return response

if __name__ == "__main__":
    import uvicorn
    # Both your app logs AND uvicorn logs will be structured JSON!
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
```

## Configuration Options

### LoggerConfig Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `override_uvicorn_loggers` | `bool` | `False` | Enable structured formatting for uvicorn loggers |
| `uvicorn_loggers` | `List[str]` | `["uvicorn", "uvicorn.access", "uvicorn.error", "uvicorn.asgi"]` | List of uvicorn loggers to override |

### Custom Uvicorn Loggers

You can customize which uvicorn loggers to override:

```python
from structured_logger import LoggerConfig, get_logger

config = LoggerConfig(
    override_uvicorn_loggers=True,
    uvicorn_loggers=[
        "uvicorn",
        "uvicorn.access",
        # Only override main and access loggers, not error/asgi
    ],
)

logger = get_logger(__name__, config=config)
```

## Log Output Examples

### Before (Plain Text)

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:52000 - "GET /users/123 HTTP/1.1" 200 OK
```

### After (Structured JSON)

```json
{"time": "2024-01-01T12:00:00.123", "level": "INFO", "message": "Started server process [12345]", "module": "uvicorn"}
{"time": "2024-01-01T12:00:00.124", "level": "INFO", "message": "Waiting for application startup.", "module": "uvicorn"}
{"time": "2024-01-01T12:00:00.125", "level": "INFO", "message": "Application startup complete.", "module": "uvicorn"}
{"time": "2024-01-01T12:00:00.126", "level": "INFO", "message": "Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)", "module": "uvicorn"}
{"time": "2024-01-01T12:00:01.000", "level": "INFO", "message": "127.0.0.1:52000 - \"GET /users/123 HTTP/1.1\" 200 OK", "module": "uvicorn.access"}
```

## Advanced Features

### Environment-Aware Formatting

The uvicorn integration respects the same environment detection as the main logger:

```python
from structured_logger import LoggerConfig, setup_uvicorn_logging

# In development: readable format
# In production: JSON format
setup_uvicorn_logging()

# Force JSON regardless of environment
setup_uvicorn_logging(force_json=True)

# Force development format regardless of environment
setup_uvicorn_logging(force_dev=True)
```

### Integration with Advanced Features

If you have advanced features enabled (async logging, correlation IDs, etc.), uvicorn loggers will automatically inherit these features:

```python
from structured_logger import LoggerConfig, get_logger
from structured_logger.advanced import CorrelationIDManager

config = LoggerConfig(
    override_uvicorn_loggers=True,
    enable_async=True,
    enable_correlation_ids=True,
)

logger = get_logger(__name__, config=config)

# Set correlation ID for request
CorrelationIDManager.set_correlation_id("req-123")

# Both your logs and uvicorn logs will include the correlation ID
await logger.info("Processing request")
```

### Sentry Integration

Uvicorn logs will also be sent to Sentry if you have Sentry integration enabled:

```python
from structured_logger import LoggerConfig, get_logger
from structured_logger.sentry_integration import SentryConfig

sentry_config = SentryConfig(
    dsn="your-sentry-dsn",
    environment="production",
)

config = LoggerConfig(
    override_uvicorn_loggers=True,
    enable_sentry=True,
    sentry_config=sentry_config,
)

logger = get_logger(__name__, config=config)
```

## Troubleshooting

### Logs Not Being Formatted

1. **Check Configuration**: Ensure `override_uvicorn_loggers=True` is set
2. **Call Order**: Make sure you call `setup_uvicorn_logging()` or configure the logger before starting uvicorn
3. **Logger Names**: Verify you're using the correct uvicorn logger names

### Duplicate Logs

If you see duplicate logs, it might be because uvicorn loggers are propagating to the root logger. The integration automatically sets `propagate=False` to prevent this.

### Performance Considerations

The uvicorn integration adds minimal overhead. However, if you're processing high-volume traffic, consider:

1. Using async logging (`enable_async=True`)
2. Implementing log sampling for access logs
3. Adjusting log levels appropriately

## Migration from Plain Uvicorn

If you're migrating from plain uvicorn logging:

1. **Before**: Uvicorn logs were plain text and hard to parse
2. **After**: All logs are structured JSON, making them easy to query and analyze
3. **Log Aggregation**: Your log aggregation tools (ELK, Splunk, etc.) can now parse uvicorn logs automatically
4. **Monitoring**: Set up alerts and dashboards based on structured uvicorn log data

## Examples

See the following example files for complete implementations:

- `examples/uvicorn_integration.py` - Basic uvicorn integration
- `examples/fastapi_advanced.py` - Advanced FastAPI with uvicorn integration

## Testing

The uvicorn integration includes comprehensive tests. Run them with:

```bash
make test
# or
uv run pytest tests/test_uvicorn_integration.py -v
```
