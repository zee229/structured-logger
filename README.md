# Structured Logger

[![PyPI version](https://badge.fury.io/py/structured-logger-railway.svg)](https://pypi.org/project/structured-logger-railway/)

A flexible, configurable structured JSON logger for Python applications. Perfect for cloud deployments, containerized applications, and log aggregation systems like ELK, Splunk, or cloud logging services.

## Features

- 🚀 **Structured JSON logging** with automatic serialization of complex objects
- ⚙️ **Highly configurable** with sensible defaults
- 🌍 **Environment-aware** formatting (JSON for production, readable for development)
- 🔧 **Custom field support** for tracing, user context, and more
- 📦 **Easy integration** with existing Python logging
- 🎯 **Type-safe** with full type hints
- 🦄 **Uvicorn integration** - automatically formats uvicorn logs as structured JSON
- 🦅 **Gunicorn integration** - automatically formats gunicorn logs as structured JSON
- ⚡ **Zero dependencies** - uses only Python standard library

## Installation

```bash
pip install structured-logger-railway
```

## Quick Start

### Basic Usage

```python
from structured_logger import get_logger

logger = get_logger(__name__)

logger.info("Application started")
logger.error("Something went wrong", extra={"user_id": "12345"})
```

**Output in development:**
```
2024-01-15 10:30:45,123 [INFO] myapp: Application started
2024-01-15 10:30:45,124 [ERROR] myapp: Something went wrong
```

**Output in production:**
```json
{"time": "2024-01-15 10:30:45,123", "level": "INFO", "message": "Application started", "module": "myapp"}
{"time": "2024-01-15 10:30:45,124", "level": "ERROR", "message": "Something went wrong", "module": "myapp", "user_id": "12345"}
```

### Custom Configuration

```python
from structured_logger import get_logger, LoggerConfig

# Custom configuration
config = LoggerConfig(
    custom_fields=["user_id", "request_id", "trace_id"],
    production_env_vars=["ENV", "ENVIRONMENT"],
    production_env_values=["prod", "production", "staging"],
    dev_format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = get_logger(__name__, config=config)
```

### Force JSON or Development Format

```python
# Always use JSON formatting
logger = get_logger(__name__, force_json=True)

# Always use development formatting
logger = get_logger(__name__, force_dev=True)
```

### Root Logger Setup

```python
from structured_logger import setup_root_logger

# Setup root logger for entire application
setup_root_logger()

# Now all loggers will use structured format
import logging
logger = logging.getLogger("myapp")
logger.info("This will be structured")
```

## Advanced Usage

### Custom Serializers

```python
from datetime import datetime
from structured_logger import LoggerConfig, get_logger

def serialize_datetime(dt):
    return dt.isoformat()

config = LoggerConfig(
    custom_serializers={
        datetime: serialize_datetime
    }
)

logger = get_logger(__name__, config=config)
logger.info("Current time", extra={"timestamp": datetime.now()})
```

### Context Fields

```python
import logging
from structured_logger import get_logger

logger = get_logger(__name__)

# Add context to log record
class ContextFilter(logging.Filter):
    def filter(self, record):
        record.user_id = getattr(self, 'user_id', None)
        record.request_id = getattr(self, 'request_id', None)
        return True

context_filter = ContextFilter()
logger.addFilter(context_filter)

# Set context
context_filter.user_id = "user123"
context_filter.request_id = "req456"

logger.info("Processing request")  # Will include user_id and request_id
```

### Exception Logging

```python
try:
    raise ValueError("Something went wrong")
except Exception:
    logger.exception("An error occurred", extra={"operation": "data_processing"})
```

**JSON Output:**
```json
{
  "time": "2024-01-15 10:30:45,123",
  "level": "ERROR", 
  "message": "An error occurred",
  "module": "myapp",
  "operation": "data_processing",
  "exception": "Traceback (most recent call last):\n  File \"example.py\", line 2, in <module>\n    raise ValueError(\"Something went wrong\")\nValueError: Something went wrong"
}
```

## Configuration Options

### LoggerConfig Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `production_env_vars` | `List[str]` | `["RAILWAY_ENVIRONMENT", "ENV", "ENVIRONMENT", "NODE_ENV"]` | Environment variables to check for production |
| `production_env_values` | `List[str]` | `["prod", "production", "staging"]` | Values that indicate production environment |
| `log_level_env_var` | `str` | `"LOG_LEVEL"` | Environment variable for log level |
| `default_log_level` | `str` | `"INFO"` | Default log level |
| `custom_fields` | `List[str]` | `["user_id", "company_id", "request_id", "trace_id", "span_id"]` | Fields to extract from log records |
| `time_format` | `Optional[str]` | `None` | Custom time format |
| `dev_format` | `str` | `"%(asctime)s [%(levelname)s] %(name)s: %(message)s"` | Format string for development |
| `custom_serializers` | `Dict[type, Callable]` | `{}` | Custom serializers for specific types |
| `include_extra_attrs` | `bool` | `True` | Whether to include extra attributes |
| `excluded_attrs` | `List[str]` | Standard logging fields | Fields to exclude from extra attributes |
| `override_uvicorn_loggers` | `bool` | `True` | Enable structured formatting for uvicorn loggers |
| `uvicorn_loggers` | `List[str]` | `["uvicorn", "uvicorn.access", "uvicorn.error", "uvicorn.asgi"]` | List of uvicorn loggers to override |
| `override_gunicorn_loggers` | `bool` | `True` | Enable structured formatting for gunicorn loggers |
| `gunicorn_loggers` | `List[str]` | `["gunicorn", "gunicorn.access", "gunicorn.error"]` | List of gunicorn loggers to override |
| `override_library_loggers` | `bool` | `True` | Enable structured formatting for third-party library loggers (httpx, sqlalchemy, etc.) |
| `library_loggers` | `List[str]` | `["httpx", "httpcore", "sqlalchemy", "starlette", "fastapi", ...]` | List of library loggers to override |

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Set logging level | `INFO` |
| `RAILWAY_ENVIRONMENT` | Railway deployment indicator | - |
| `ENV` | Environment indicator | - |
| `ENVIRONMENT` | Environment indicator | - |
| `NODE_ENV` | Node.js style environment | - |

## Framework Integration

### Flask with Gunicorn Integration

```python
from flask import Flask, request, g
from structured_logger import get_logger, setup_gunicorn_logging
import uuid

# Option 1: Simple gunicorn setup (recommended)
setup_gunicorn_logging(force_json=True)

# Option 2: Full configuration with gunicorn override
config = LoggerConfig(
    override_gunicorn_loggers=True,  # Enable structured gunicorn logs
    custom_fields=["request_id", "user_id"],
    include_extra_attrs=True,
)

app = Flask(__name__)
logger = get_logger(__name__, config=config)

@app.before_request
def before_request():
    g.request_id = str(uuid.uuid4())

@app.after_request
def after_request(response):
    logger.info(
        "Request processed",
        extra={
            "request_id": getattr(g, 'request_id', None),
            "method": request.method,
            "path": request.path,
            "status": response.status_code
        }
    )
    return response

# Run with: gunicorn --workers 4 --bind 0.0.0.0:8000 myapp:app
# Gunicorn access logs and error logs will now be structured JSON!
```

### Automatic Logger Overrides (Enabled by Default!)

**All server and library logs are automatically formatted as JSON!** This includes:
- **Uvicorn**: `uvicorn`, `uvicorn.access`, `uvicorn.error`, `uvicorn.asgi`
- **Gunicorn**: `gunicorn`, `gunicorn.access`, `gunicorn.error`
- **HTTP Clients**: `httpx`, `httpcore`, `urllib3`, `requests`, `aiohttp`
- **Database**: `sqlalchemy` (including engine, pool, orm)
- **Frameworks**: `starlette`, `fastapi`
- **Async**: `asyncio`

```python
from structured_logger import get_logger

# That's it! Everything is automatic!
logger = get_logger(__name__)

# All logs are now JSON formatted:
# ✓ Your application logs
# ✓ Uvicorn/Gunicorn logs (automatic!)
# ✓ Third-party library logs (automatic!)
```

**To disable specific overrides:**

```python
from structured_logger import LoggerConfig, get_logger

config = LoggerConfig(
    override_uvicorn_loggers=False,   # Disable uvicorn override
    override_gunicorn_loggers=False,  # Disable gunicorn override
    override_library_loggers=False,   # Disable library override
)
logger = get_logger(__name__, config=config)
```

### FastAPI with Uvicorn Integration

```python
from fastapi import FastAPI, Request
from structured_logger import get_logger
import uuid
import time

# Simple setup - everything is automatic!
logger = get_logger(__name__)

# Or with custom fields
from structured_logger import LoggerConfig

config = LoggerConfig(
    custom_fields=["request_id", "user_id"],
    include_extra_attrs=True,
    # All overrides are enabled by default:
    # override_uvicorn_loggers=True
    # override_library_loggers=True
    # override_gunicorn_loggers=True
)

app = FastAPI()
logger = get_logger(__name__, config=config)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        "Request processed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration": process_time
        }
    )
    
    return response

if __name__ == "__main__":
    import uvicorn
    # Uvicorn access logs and error logs will now be structured JSON!
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Django

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'structured': {
            'level': 'INFO',
            'class': 'structured_logger.logger.StructuredLogHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['structured'],
            'level': 'INFO',
            'propagate': True,
        },
        'myapp': {
            'handlers': ['structured'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## Railway.app Compatibility

This library maintains full compatibility with Railway.app deployments. The original Railway-specific functionality is preserved:

```python
# These work exactly like before
from structured_logger import get_railway_logger

logger = get_railway_logger(__name__)
logger.info("Deployed to Railway!")
```

## Development

```bash
# Clone the repository
git clone https://github.com/zee229/structured-logger.git
cd structured-logger

# Install development dependencies
pip install -e .

# Run examples
python examples/basic_usage.py
python examples/custom_config.py
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Uvicorn Integration

New in v1.3.0! Automatically format uvicorn logs as structured JSON for better log parsing and analysis.

### Quick Setup

```python
from structured_logger import setup_uvicorn_logging

# This will override all uvicorn loggers with structured formatting
setup_uvicorn_logging(force_json=True)
```

### Configuration Options

```python
from structured_logger import LoggerConfig, get_logger

config = LoggerConfig(
    override_uvicorn_loggers=True,  # Enable uvicorn override
    uvicorn_loggers=[               # Customize which loggers to override
        "uvicorn",
        "uvicorn.access", 
        "uvicorn.error",
        "uvicorn.asgi"
    ],
    custom_fields=["request_id", "user_id"],
)

logger = get_logger(__name__, config=config)
```

### What Gets Formatted

With uvicorn integration enabled, these logs are automatically structured:

- **uvicorn**: Main uvicorn logger
- **uvicorn.access**: HTTP access logs
- **uvicorn.error**: Error logs
- **uvicorn.asgi**: ASGI-related logs

**Before (plain text):**
```
INFO:     127.0.0.1:52000 - "GET /users/123 HTTP/1.1" 200 OK
```

**After (structured JSON):**
```json
{"time": "2024-01-01T12:00:00", "level": "INFO", "message": "127.0.0.1:52000 - \"GET /users/123 HTTP/1.1\" 200 OK", "module": "uvicorn.access"}
```

## Changelog

### 1.3.0
- ✨ **New**: Uvicorn logger integration for structured FastAPI logs
- 🔧 Added `setup_uvicorn_logging()` convenience function
- 📝 Enhanced documentation with uvicorn examples
- 🧪 Comprehensive test coverage for uvicorn integration

### 1.0.0
- Initial release
- Flexible configuration system
- Environment-aware formatting
- Custom serializers support
- Full backward compatibility with Railway logger
