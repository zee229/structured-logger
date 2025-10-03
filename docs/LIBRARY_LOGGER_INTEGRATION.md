# Third-Party Library Logger Integration

## Overview

The structured-logger package now automatically formats logs from third-party libraries as structured JSON. This feature is **enabled by default** to provide a seamless logging experience across your entire application stack.

## Supported Libraries

The following libraries are automatically configured with structured logging:

- **HTTP Clients**: `httpx`, `httpcore`, `urllib3`, `requests`, `aiohttp`
- **Database**: `sqlalchemy` (including `sqlalchemy.engine`, `sqlalchemy.pool`, `sqlalchemy.orm`)
- **Web Frameworks**: `starlette`, `fastapi`
- **Async Runtime**: `asyncio`

## Quick Start

### Automatic (Default Behavior)

Library logging is enabled by default. Just set up your logger normally:

```python
from structured_logger import LoggerConfig, setup_root_logger

# Library loggers are automatically formatted!
setup_root_logger(config=LoggerConfig(override_uvicorn_loggers=True))
```

**Result**: All logs from your app, uvicorn, and third-party libraries will be JSON formatted.

### Disable Library Logging

If you want to keep library logs in their original format:

```python
from structured_logger import LoggerConfig, setup_root_logger

config = LoggerConfig(
    override_library_loggers=False,  # Disable automatic library formatting
    override_uvicorn_loggers=True,   # Still format uvicorn logs
)
setup_root_logger(config=config)
```

## Configuration Options

### LoggerConfig Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `override_library_loggers` | `bool` | `True` | Enable structured formatting for library loggers |
| `library_loggers` | `List[str]` | See below | List of library logger names to override |

### Default Library Loggers

```python
[
    "httpx",
    "httpcore",
    "sqlalchemy",
    "sqlalchemy.engine",
    "sqlalchemy.pool",
    "sqlalchemy.orm",
    "starlette",
    "fastapi",
    "asyncio",
    "aiohttp",
    "urllib3",
    "requests",
]
```

## Advanced Usage

### Custom Library Logger List

Override only specific libraries:

```python
from structured_logger import LoggerConfig, setup_root_logger

config = LoggerConfig(
    override_library_loggers=True,
    library_loggers=["httpx", "sqlalchemy", "mylib"],  # Custom list
)
setup_root_logger(config=config)
```

### Using the Convenience Function

For standalone library logger setup:

```python
from structured_logger import setup_library_logging

# Simple setup
setup_library_logging(force_json=True)

# With custom config
from structured_logger import LoggerConfig

config = LoggerConfig(
    custom_fields=["request_id", "user_id"],
    library_loggers=["httpx", "sqlalchemy"],
)
setup_library_logging(config=config, force_json=True)
```

## Complete FastAPI Example

```python
from fastapi import FastAPI, Request
from structured_logger import LoggerConfig, get_logger, setup_root_logger

# Simple one-line setup
setup_root_logger(config=LoggerConfig(override_uvicorn_loggers=True))

logger = get_logger(__name__)
app = FastAPI()


@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return {"message": "Hello World"}


@app.get("/test-library-logs")
async def test_library_logs():
    import logging
    
    # These will all be JSON formatted automatically!
    httpx_logger = logging.getLogger("httpx")
    httpx_logger.info("HTTP client log")
    
    sqlalchemy_logger = logging.getLogger("sqlalchemy")
    sqlalchemy_logger.info("Database log")
    
    return {"message": "Check logs - all formatted as JSON!"}


if __name__ == "__main__":
    import uvicorn
    
    # All logs are now structured JSON:
    # ✓ Your application logs
    # ✓ Uvicorn server logs
    # ✓ Third-party library logs (automatic!)
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Benefits

### Before (Without Library Logger Override)

```
2025-10-03 12:45:19 [INFO] myapp: Application started
HTTP Request: POST http://api.example.com/data "HTTP/1.1 200 OK"
2025-10-03 12:45:20 [INFO] myapp: Request completed
```

Mixed formats make parsing difficult!

### After (With Library Logger Override - Default)

```json
{"time": "2025-10-03 12:45:19", "level": "INFO", "message": "Application started", "module": "myapp"}
{"time": "2025-10-03 12:45:19", "level": "INFO", "message": "HTTP Request: POST http://api.example.com/data \"HTTP/1.1 200 OK\"", "module": "httpx"}
{"time": "2025-10-03 12:45:20", "level": "INFO", "message": "Request completed", "module": "myapp"}
```

Consistent JSON format across all logs!

## Troubleshooting

### Library Logs Still Not Formatted

1. **Check Configuration**: Ensure `override_library_loggers=True` (it's the default)
2. **Call Order**: Make sure you call `setup_root_logger()` or `get_logger()` before the library creates its loggers
3. **Logger Names**: Verify the library logger name matches your configuration

### Too Many Logs

Adjust the log level for library loggers:

```python
import os

# Set log level via environment variable
os.environ["LOG_LEVEL"] = "WARNING"

# Or in config
config = LoggerConfig(
    override_library_loggers=True,
    default_log_level="WARNING",  # Only WARNING and above
)
```

### Disable for Specific Libraries

```python
# Keep httpx logs in original format, but format sqlalchemy
config = LoggerConfig(
    override_library_loggers=True,
    library_loggers=["sqlalchemy"],  # Only override sqlalchemy
)
```

## Testing

The library logger integration includes comprehensive tests in `tests/test_library_logger_integration.py`:

```bash
# Run library logger tests
uv run pytest tests/test_library_logger_integration.py -v

# Run all tests
uv run pytest -v
```

## Version History

- **v1.4.0**: Added third-party library logger integration (enabled by default)
- **v1.3.0**: Added uvicorn logger integration
- **v1.3.1**: Added gunicorn logger integration

## See Also

- [Uvicorn Integration](UVICORN_INTEGRATION.md)
- [Gunicorn Integration](GUNICORN_INTEGRATION.md)
- [Main README](../README.md)
