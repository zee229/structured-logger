# Third-Party Library Logger Integration

## Overview

The structured-logger package now automatically formats logs from third-party libraries as structured JSON. This feature is **enabled by default** to provide a seamless logging experience across your entire application stack.

## Supported Libraries

The following libraries are automatically configured with structured logging at WARNING level by default:

- **HTTP Clients**: `httpx`, `httpcore`, `urllib3`, `requests`, `aiohttp`
- **Web Frameworks**: `starlette`, `fastapi`
- **Async Runtime**: `asyncio`

**Note**: SQLAlchemy and LangChain have separate control mechanisms (see their respective sections in CLAUDE.md).

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
| `enable_library_logging` | `bool` | `True` | Enable/disable library logging completely (False = silence) |
| `library_log_level` | `str` | `"WARNING"` | Log level for libraries (independent from app level) |
| `library_log_level_env_var` | `str` | `"LIBRARY_LOG_LEVEL"` | Environment variable name for runtime config |
| `library_loggers` | `List[str]` | See below | List of library logger names to override |

### Default Library Loggers

```python
[
    "httpx",
    "httpcore",
    "starlette",
    "fastapi",
    "asyncio",
    "aiohttp",
    "urllib3",
    "requests",
]
```

**Note**: SQLAlchemy loggers are managed separately via `enable_sqlalchemy_logging` and `sqlalchemy_log_level`.

## Advanced Usage

### Independent Log Level Control (New in v1.6.0)

Control library log levels independently from your application's log level:

```python
import os
from structured_logger import LoggerConfig, get_logger

# Method 1: Environment variables (most flexible)
os.environ["LOG_LEVEL"] = "DEBUG"  # App at DEBUG
os.environ["LIBRARY_LOG_LEVEL"] = "WARNING"  # Libraries at WARNING (default)

logger = get_logger(__name__)
logger.debug("App debug message")  # ✓ Shows
# httpcore.debug() messages won't show  # ✗ Hidden

# Method 2: Config object
config = LoggerConfig(
    default_log_level="DEBUG",  # App log level
    library_log_level="ERROR",  # Library log level (only errors)
)
logger = get_logger(__name__, config=config)

# Method 3: Completely silence libraries
config = LoggerConfig(
    enable_library_logging=False,  # Silence all library logs
)
logger = get_logger(__name__, config=config)
```

**Why this is useful**: Libraries like httpx and httpcore generate extremely verbose debug logs. With independent control, you can:
- Debug your application code with `LOG_LEVEL=DEBUG`
- Keep library logs at WARNING to avoid spam
- See library errors when they occur
- Completely silence libraries in production

### Custom Library Logger List

Override only specific libraries:

```python
from structured_logger import LoggerConfig, setup_root_logger

config = LoggerConfig(
    override_library_loggers=True,
    library_loggers=["httpx", "httpcore", "mylib"],  # Custom list
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

### Too Many Logs / Library Debug Spam

**New in v1.6.0**: Library log level is now independent from your app log level!

```python
import os

# Set library log level via environment variable
os.environ["LIBRARY_LOG_LEVEL"] = "ERROR"  # Only show errors from libraries
os.environ["LOG_LEVEL"] = "DEBUG"  # Your app can still use DEBUG

# Or in config
config = LoggerConfig(
    library_log_level="ERROR",  # Libraries: errors only
    default_log_level="DEBUG",  # Your app: debug level
)

# Completely silence library logs
config = LoggerConfig(
    enable_library_logging=False,  # No library logs at all
)
```

**Common scenario**: You want to debug your app with `LOG_LEVEL=DEBUG` but don't want to see httpcore/httpx debug spam:

```python
import os

# Your app logs at DEBUG, but libraries stay at WARNING (default)
os.environ["LOG_LEVEL"] = "DEBUG"  # App log level
# LIBRARY_LOG_LEVEL defaults to "WARNING" - no need to set it!

from structured_logger import get_logger

logger = get_logger(__name__)
logger.debug("This will show")  # ✓ Shows (app at DEBUG)

# Meanwhile, httpcore.debug() won't show (library at WARNING)
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

- **v1.6.0**: Added independent log level control for libraries (`library_log_level`, `enable_library_logging`, `LIBRARY_LOG_LEVEL` env var)
- **v1.4.0**: Added third-party library logger integration (enabled by default)
- **v1.3.1**: Added gunicorn logger integration
- **v1.3.0**: Added uvicorn logger integration

## See Also

- [Uvicorn Integration](UVICORN_INTEGRATION.md)
- [Gunicorn Integration](GUNICORN_INTEGRATION.md)
- [Main README](../README.md)
