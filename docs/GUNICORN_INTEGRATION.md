# Gunicorn Integration Guide

The structured-logger package includes built-in support for formatting Gunicorn logs as structured JSON. This is particularly useful for Flask applications where you want consistent log formatting across both your application logs and the web server logs.

## Overview

When you enable Gunicorn integration, the following loggers are automatically configured to use structured JSON formatting:

- `gunicorn` - Main Gunicorn logger
- `gunicorn.access` - HTTP access logs (requests/responses)
- `gunicorn.error` - Error logs

## Quick Start

### Method 1: Simple Setup (Recommended)

```python
from structured_logger import setup_gunicorn_logging

# This will override all Gunicorn loggers with structured formatting
setup_gunicorn_logging(force_json=True)
```

### Method 2: Configuration-Based Setup

```python
from structured_logger import LoggerConfig, get_logger

config = LoggerConfig(
    override_gunicorn_loggers=True,  # Enable Gunicorn override
    custom_fields=["request_id", "user_id", "trace_id"],
    include_extra_attrs=True,
)

logger = get_logger(__name__, config=config)
```

## Flask Integration Example

```python
from flask import Flask, Request, g
from structured_logger import setup_gunicorn_logging, get_logger
import uuid
import time

# Setup Gunicorn logging first
setup_gunicorn_logging(force_json=True)

app = Flask(__name__)
logger = get_logger(__name__, force_json=True)

@app.before_request
def before_request():
    g.request_id = str(uuid.uuid4())
    g.start_time = time.time()
    
    logger.info(
        "Request started",
        extra={
            "request_id": g.request_id,
            "method": request.method,
            "path": request.url.path,
        }
    )

@app.after_request
def after_request(response):
    duration = time.time() - g.start_time
    logger.info(
        "Request completed",
        extra={
            "request_id": g.request_id,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
        }
    )
    return response

if __name__ == "__main__":
    import gunicorn.app.base
    # Both your app logs AND Gunicorn logs will be structured JSON!
```

## Running with Gunicorn

### Basic Command

```bash
gunicorn --workers 4 --bind 0.0.0.0:8000 myapp:app
```

### With Logging Configuration

```bash
gunicorn --workers 4 \
         --bind 0.0.0.0:8000 \
         --log-level info \
         --access-logfile - \
         --error-logfile - \
         myapp:app
```

### Production Configuration

```bash
gunicorn --workers 4 \
         --worker-class gevent \
         --bind 0.0.0.0:8000 \
         --log-level info \
         --access-logfile - \
         --error-logfile - \
         --timeout 120 \
         myapp:app
```

## Configuration Options

### LoggerConfig Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `override_gunicorn_loggers` | `bool` | `False` | Enable structured formatting for Gunicorn loggers |
| `gunicorn_loggers` | `List[str]` | `["gunicorn", "gunicorn.access", "gunicorn.error"]` | List of Gunicorn loggers to override |

### Custom Gunicorn Loggers

You can customize which Gunicorn loggers to override:

```python
from structured_logger import LoggerConfig, get_logger

config = LoggerConfig(
    override_gunicorn_loggers=True,
    gunicorn_loggers=[
        "gunicorn",
        "gunicorn.access",
        # Only override main and access loggers, not error
    ],
)

logger = get_logger(__name__, config=config)
```

## Log Output Examples

### Before (Plain Text)

```
[2024-01-01 12:00:00 +0000] [12345] [INFO] Starting gunicorn 20.1.0
[2024-01-01 12:00:00 +0000] [12345] [INFO] Listening at: http://0.0.0.0:8000 (12345)
[2024-01-01 12:00:00 +0000] [12345] [INFO] Using worker: sync
[2024-01-01 12:00:01 +0000] [12346] [INFO] Booting worker with pid: 12346
127.0.0.1 - - [01/Jan/2024:12:00:05 +0000] "GET /users/123 HTTP/1.1" 200 1234 "-" "Mozilla/5.0"
```

### After (Structured JSON)

```json
{"time": "2024-01-01 12:00:00,000", "level": "INFO", "message": "Starting gunicorn 20.1.0", "module": "gunicorn"}
{"time": "2024-01-01 12:00:00,001", "level": "INFO", "message": "Listening at: http://0.0.0.0:8000 (12345)", "module": "gunicorn"}
{"time": "2024-01-01 12:00:00,002", "level": "INFO", "message": "Using worker: sync", "module": "gunicorn"}
{"time": "2024-01-01 12:00:01,000", "level": "INFO", "message": "Booting worker with pid: 12346", "module": "gunicorn"}
{"time": "2024-01-01 12:00:05,000", "level": "INFO", "message": "127.0.0.1 - - \"GET /users/123 HTTP/1.1\" 200 1234", "module": "gunicorn.access"}
```

## Advanced Features

### Environment-Aware Formatting

The Gunicorn integration respects the same environment detection as the main logger:

```python
from structured_logger import setup_gunicorn_logging

# In development: readable format
# In production: JSON format
setup_gunicorn_logging()

# Force JSON regardless of environment
setup_gunicorn_logging(force_json=True)

# Force development format regardless of environment
setup_gunicorn_logging(force_dev=True)
```

### Integration with Advanced Features

If you have advanced features enabled (async logging, correlation IDs, etc.), Gunicorn loggers will automatically inherit these features:

```python
from structured_logger import LoggerConfig, get_logger
from structured_logger.advanced import CorrelationIDManager

config = LoggerConfig(
    override_gunicorn_loggers=True,
    enable_async=True,
    enable_correlation_ids=True,
)

logger = get_logger(__name__, config=config)

# Set correlation ID for request
CorrelationIDManager.set_correlation_id("req-123")

# Both your logs and Gunicorn logs will include the correlation ID
await logger.info("Processing request")
```

### Sentry Integration

Gunicorn logs will also be sent to Sentry if you have Sentry integration enabled:

```python
from structured_logger import LoggerConfig, get_logger
from structured_logger.sentry_integration import SentryConfig

sentry_config = SentryConfig(
    dsn="your-sentry-dsn",
    environment="production",
)

config = LoggerConfig(
    override_gunicorn_loggers=True,
    enable_sentry=True,
    sentry_config=sentry_config,
)

logger = get_logger(__name__, config=config)
```

## Railway Deployment

When deploying to Railway with Gunicorn, structured logging works seamlessly:

```python
# app.py
from structured_logger import setup_gunicorn_logging, get_logger

# Setup structured logging for Gunicorn
setup_gunicorn_logging(force_json=True)

app = create_app()
logger = get_logger(__name__, force_json=True)
```

Then in your Railway deployment, use Gunicorn:

```bash
# Procfile or railway.toml
gunicorn --workers 4 --bind 0.0.0.0:$PORT app:app
```

All logs (both application and Gunicorn) will appear as structured JSON in Railway's log viewer, making them easy to search and filter.

## Troubleshooting

### Logs Not Being Formatted

1. **Check Configuration**: Ensure `override_gunicorn_loggers=True` is set
2. **Call Order**: Make sure you call `setup_gunicorn_logging()` or configure the logger before starting Gunicorn
3. **Logger Names**: Verify you're using the correct Gunicorn logger names

### Duplicate Logs

If you see duplicate logs, it might be because Gunicorn loggers are propagating to the root logger. The integration automatically sets `propagate=False` to prevent this.

### Gunicorn Access Logs Not Showing

Make sure you're directing Gunicorn's access logs to stdout/stderr:

```bash
gunicorn --access-logfile - --error-logfile - myapp:app
```

### Performance Considerations

The Gunicorn integration adds minimal overhead. However, if you're processing high-volume traffic, consider:

1. Using async logging (`enable_async=True`)
2. Implementing log sampling for access logs
3. Adjusting log levels appropriately
4. Using appropriate worker types (gevent, uvloop)

## Migration from Plain Gunicorn

If you're migrating from plain Gunicorn logging:

1. **Before**: Gunicorn logs were plain text and hard to parse
2. **After**: All logs are structured JSON, making them easy to query and analyze
3. **Log Aggregation**: Your log aggregation tools (ELK, Splunk, Datadog, etc.) can now parse Gunicorn logs automatically
4. **Monitoring**: Set up alerts and dashboards based on structured Gunicorn log data

## Comparison with Uvicorn

Both Uvicorn and Gunicorn integrations work similarly:

| Feature | Uvicorn | Gunicorn |
|---------|---------|----------|
| Structured JSON logs | ✅ | ✅ |
| Access log formatting | ✅ | ✅ |
| Error log formatting | ✅ | ✅ |
| Sentry integration | ✅ | ✅ |
| Correlation IDs | ✅ | ✅ |
| Async logging | ✅ | ✅ |

You can even use both if you're running Gunicorn with Uvicorn workers:

```python
from structured_logger import setup_gunicorn_logging, setup_uvicorn_logging

# Setup both
setup_gunicorn_logging(force_json=True)
setup_uvicorn_logging(force_json=True)
```

## Examples

See the following example files for complete implementations:

- `examples/gunicorn_integration.py` - Basic Gunicorn integration
- `examples/flask_advanced.py` - Advanced Flask with Gunicorn integration

## Testing

The Gunicorn integration includes comprehensive tests. Run them with:

```bash
make test
# or
uv run pytest tests/test_gunicorn_integration.py -v
```

## Best Practices

1. **Always call setup first**: Call `setup_gunicorn_logging()` before creating your Flask/Django app
2. **Use force_json in production**: Ensure consistent JSON formatting in production environments
3. **Include request IDs**: Add correlation/request IDs to track requests across logs
4. **Configure log levels**: Use appropriate log levels for different environments
5. **Monitor performance**: Keep an eye on logging overhead in high-traffic scenarios
6. **Use log aggregation**: Send structured logs to a centralized logging system
