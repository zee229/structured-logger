# Default Logger Overrides - Summary

## Overview

As of v1.4.0, **all logger overrides are enabled by default** for maximum convenience. This means structured JSON logging works automatically across your entire application stack with zero configuration.

## What Changed

### Before (v1.3.x)
```python
# Required explicit configuration
config = LoggerConfig(
    override_uvicorn_loggers=True,   # Had to enable
    override_gunicorn_loggers=True,  # Had to enable
    override_library_loggers=True,   # Had to enable
)
logger = get_logger(__name__, config=config)
```

### After (v1.4.0+)
```python
# Everything is automatic!
logger = get_logger(__name__)

# All logs are now JSON formatted:
# ✓ Your application logs
# ✓ Uvicorn server logs (automatic!)
# ✓ Gunicorn server logs (automatic!)
# ✓ Third-party library logs (automatic!)
```

## Default Configuration Values

| Parameter | Old Default | New Default | Description |
|-----------|-------------|-------------|-------------|
| `override_uvicorn_loggers` | `False` | `True` | Uvicorn server logs |
| `override_gunicorn_loggers` | `False` | `True` | Gunicorn server logs |
| `override_library_loggers` | N/A | `True` | Third-party library logs |

## Covered Loggers

### Server Loggers (Automatic)
- **Uvicorn**: `uvicorn`, `uvicorn.access`, `uvicorn.error`, `uvicorn.asgi`
- **Gunicorn**: `gunicorn`, `gunicorn.access`, `gunicorn.error`

### Library Loggers (Automatic)
- **HTTP Clients**: `httpx`, `httpcore`, `urllib3`, `requests`, `aiohttp`
- **Database**: `sqlalchemy`, `sqlalchemy.engine`, `sqlalchemy.pool`, `sqlalchemy.orm`
- **Frameworks**: `starlette`, `fastapi`
- **Async**: `asyncio`

## Usage Examples

### Minimal Setup (Recommended)

```python
from structured_logger import get_logger

# That's it! Everything works automatically
logger = get_logger(__name__)

logger.info("Hello World")
# Output: {"time": "...", "level": "INFO", "message": "Hello World", "module": "..."}
```

### With Custom Fields

```python
from structured_logger import LoggerConfig, get_logger

config = LoggerConfig(
    custom_fields=["request_id", "user_id"],
    # All overrides are already enabled by default!
)

logger = get_logger(__name__, config=config)
logger.info("Request received", extra={"request_id": "123"})
```

### Disable Specific Overrides

If you want to keep some logs in their original format:

```python
from structured_logger import LoggerConfig, get_logger

config = LoggerConfig(
    override_uvicorn_loggers=True,    # Keep uvicorn JSON
    override_gunicorn_loggers=False,  # Disable gunicorn override
    override_library_loggers=False,   # Disable library override
)

logger = get_logger(__name__, config=config)
```

### Disable All Overrides

To use only structured logging for your app logs:

```python
from structured_logger import LoggerConfig, get_logger

config = LoggerConfig(
    override_uvicorn_loggers=False,
    override_gunicorn_loggers=False,
    override_library_loggers=False,
)

logger = get_logger(__name__, config=config)
# Only your app logs will be JSON formatted
```

## FastAPI Complete Example

```python
from fastapi import FastAPI
from structured_logger import get_logger

# One line setup!
logger = get_logger(__name__)

app = FastAPI()

@app.get("/")
async def root():
    logger.info("Request received")
    return {"message": "Hello World"}

if __name__ == "__main__":
    import uvicorn
    
    # All logs are automatically JSON formatted:
    # ✓ Your app logs (logger.info)
    # ✓ Uvicorn access logs
    # ✓ Uvicorn error logs
    # ✓ Any httpx/sqlalchemy/starlette logs
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Migration Guide

### From v1.3.x to v1.4.0

**No breaking changes!** Your existing code will continue to work.

#### If you were using explicit overrides:
```python
# v1.3.x - Still works in v1.4.0
config = LoggerConfig(
    override_uvicorn_loggers=True,  # Redundant but harmless
)
```

#### Simplify to:
```python
# v1.4.0 - Cleaner
logger = get_logger(__name__)
```

#### If you explicitly disabled overrides:
```python
# v1.3.x
config = LoggerConfig(
    override_uvicorn_loggers=False,  # This was the default
)
```

**Action required**: If you want to keep overrides disabled, you must now explicitly set them to `False`:
```python
# v1.4.0
config = LoggerConfig(
    override_uvicorn_loggers=False,   # Now required to disable
    override_gunicorn_loggers=False,  # Now required to disable
    override_library_loggers=False,   # Now required to disable
)
```

## Benefits

### 1. Zero Configuration
```python
# Just import and use!
from structured_logger import get_logger
logger = get_logger(__name__)
```

### 2. Consistent Logging
All logs across your entire stack are formatted consistently as JSON, making parsing and analysis trivial.

### 3. Production Ready
Perfect for cloud deployments, containerized applications, and log aggregation systems (ELK, Splunk, Datadog, etc.).

### 4. Developer Friendly
In development, logs automatically use readable format. In production, they automatically use JSON format.

## Testing

All tests have been updated to reflect the new defaults:
- `test_uvicorn_integration.py` - ✓ 9 tests pass
- `test_gunicorn_integration.py` - ✓ 15 tests pass
- `test_library_logger_integration.py` - ✓ 15 tests pass

Run tests:
```bash
uv run pytest tests/test_*_integration.py -v
```

## Troubleshooting

### Too Many Logs?

Increase the log level:
```python
import os
os.environ["LOG_LEVEL"] = "WARNING"

# Or in config
config = LoggerConfig(default_log_level="WARNING")
```

### Want Original Format for Some Loggers?

Disable specific overrides:
```python
config = LoggerConfig(
    override_library_loggers=False,  # Keep library logs as-is
)
```

### Custom Library List

Override only specific libraries:
```python
config = LoggerConfig(
    library_loggers=["httpx", "sqlalchemy"],  # Only these
)
```

## Version History

- **v1.4.0**: All logger overrides enabled by default
- **v1.3.1**: Added gunicorn logger integration
- **v1.3.0**: Added uvicorn logger integration
- **v1.2.0**: Initial release

## See Also

- [Library Logger Integration](LIBRARY_LOGGER_INTEGRATION.md)
- [Uvicorn Integration](UVICORN_INTEGRATION.md)
- [Gunicorn Integration](GUNICORN_INTEGRATION.md)
- [Main README](../README.md)
