# Sentry Integration for Structured Logger

This document provides comprehensive information about integrating Sentry error monitoring with the structured logger package.

## Overview

The Sentry integration allows you to automatically send error logs to Sentry while maintaining your existing Railway-compatible JSON logging format. This integration is designed to be:

- **Non-intrusive**: Works alongside existing log handlers without interfering with Railway formatting
- **Configurable**: Extensive configuration options for different use cases
- **Optional**: Can be enabled/disabled without affecting core logging functionality
- **Context-rich**: Automatically includes structured log context in Sentry events

## Installation

Install the structured logger with Sentry support:

```bash
# Install with Sentry integration
pip install structured-logger-railway[sentry]

# Or install Sentry SDK separately
pip install structured-logger-railway sentry-sdk
```

## Quick Start

### Basic Setup

```python
import os
from structured_logger import get_logger, LoggerConfig, SentryConfig

# Configure Sentry integration
sentry_config = SentryConfig(
    dsn=os.getenv("SENTRY_DSN"),  # Your Sentry DSN
    min_level=logging.ERROR,      # Only send ERROR and above
    environment="production"
)

# Configure logger with Sentry
logger_config = LoggerConfig(
    enable_sentry=True,
    sentry_config=sentry_config
)

# Get logger
logger = get_logger("my_app", config=logger_config)

# Use normally - errors will automatically go to Sentry
logger.info("This goes to console/Railway only")
logger.error("This goes to both console/Railway AND Sentry")
```

### Environment Variables

Set these environment variables for easy configuration:

```bash
export SENTRY_DSN="https://your-dsn@sentry.io/project-id"
export SENTRY_ENVIRONMENT="production"
export SENTRY_RELEASE="1.0.0"
```

## Configuration

### SentryConfig Options

```python
from structured_logger import SentryConfig
import logging

sentry_config = SentryConfig(
    # Required: Sentry DSN (can also use SENTRY_DSN env var)
    dsn="https://your-dsn@sentry.io/project-id",
    
    # Minimum log level to send to Sentry (default: ERROR)
    min_level=logging.ERROR,
    
    # Whether to send personally identifiable information
    send_default_pii=True,
    
    # Performance monitoring sample rate (0.0 to 1.0)
    traces_sample_rate=0.1,
    
    # Environment name (can also use SENTRY_ENVIRONMENT env var)
    environment="production",
    
    # Release version (can also use SENTRY_RELEASE env var)
    release="1.0.0",
    
    # Whether to enable Sentry's automatic logging integration
    # (not recommended with structured logging)
    enable_logging_integration=False,
    
    # Additional Sentry integrations
    additional_integrations=[],
    
    # Default tags for all Sentry events
    default_tags={
        "service": "my-service",
        "component": "api"
    },
    
    # Log record fields to include as Sentry tags
    tag_fields=["user_id", "company_id", "request_id", "correlation_id"],
    
    # Log record fields to include as Sentry extra context
    extra_fields=["module", "funcName", "lineno", "pathname"]
)
```

### LoggerConfig Integration

```python
from structured_logger import LoggerConfig, SentryConfig

logger_config = LoggerConfig(
    # Enable Sentry integration
    enable_sentry=True,
    
    # Sentry configuration
    sentry_config=sentry_config,
    
    # Other logger settings work normally
    custom_fields=["user_id", "company_id", "request_id"],
    enable_correlation_ids=True,
    
    # Can combine with other advanced features
    enable_async=True,
    enable_metrics=True
)
```

## Usage Examples

### Automatic Error Reporting

```python
logger = get_logger("my_app", config=logger_config)

# This will be sent to Sentry automatically
logger.error("Database connection failed", extra={
    "user_id": "user123",
    "company_id": "company456", 
    "database": "primary",
    "retry_count": 3
})

# Exception logging with stack traces
try:
    result = risky_operation()
except Exception as e:
    logger.exception("Operation failed", extra={
        "user_id": "user123",
        "operation": "data_processing",
        "input_size": len(data)
    })
```

### Manual Sentry Capture

```python
from structured_logger import (
    capture_exception_with_context,
    capture_message_with_context
)

# Capture exception with rich context
try:
    process_payment(amount, card)
except PaymentError as e:
    event_id = capture_exception_with_context(
        exception=e,
        user_id="user123",
        company_id="company456",
        transaction_id="txn_789",
        amount=amount,
        payment_method="credit_card"
    )
    print(f"Error reported to Sentry: {event_id}")

# Capture custom message
event_id = capture_message_with_context(
    message="Critical business metric threshold exceeded",
    level="warning",
    user_id="user123",
    metric_name="conversion_rate",
    current_value=0.02,
    threshold=0.05
)
```

### User Context and Tags

```python
from structured_logger import set_sentry_user, set_sentry_context

# Set user context (persists for all subsequent events)
set_sentry_user(
    user_id="user123",
    email="user@example.com",
    username="johndoe",
    subscription_plan="premium"
)

# Set custom context
set_sentry_context("business", {
    "company_id": "company456",
    "plan": "enterprise",
    "feature_flags": ["new_ui", "beta_analytics"]
})
```

### Breadcrumbs for Debugging

```python
from structured_logger import add_sentry_breadcrumb

# Add breadcrumbs to track user actions
add_sentry_breadcrumb(
    message="User started checkout process",
    category="user_action",
    level="info",
    data={"cart_items": 3, "total_amount": 99.99}
)

add_sentry_breadcrumb(
    message="Payment validation started",
    category="business_logic",
    level="info",
    data={"payment_method": "credit_card"}
)

# When an error occurs, breadcrumbs provide context
logger.error("Payment processing failed")
```

## Advanced Features

### Integration with Correlation IDs

```python
from structured_logger import LoggerConfig, CorrelationIDManager

logger_config = LoggerConfig(
    enable_sentry=True,
    enable_correlation_ids=True,
    sentry_config=sentry_config
)

logger = get_logger("my_app", config=logger_config)

# Use correlation context
with CorrelationIDManager.correlation_context() as correlation_id:
    logger.info("Processing request", extra={"user_id": "user123"})
    
    # This error will include the correlation_id in Sentry
    logger.error("Request processing failed")
```

### Async Logging with Sentry

```python
logger_config = LoggerConfig(
    enable_sentry=True,
    enable_async=True,  # Enable async logging
    sentry_config=sentry_config
)

async_logger = get_logger("my_app", config=logger_config)

# Async logging methods
await async_logger.error("Async error occurred")
```

### Custom Serialization

```python
from datetime import datetime
from structured_logger import LoggerConfig

def serialize_datetime(dt):
    return dt.isoformat()

logger_config = LoggerConfig(
    enable_sentry=True,
    sentry_config=sentry_config,
    custom_serializers={
        datetime: serialize_datetime
    }
)
```

## Environment-Specific Configuration

### Development Environment

```python
# Disable Sentry in development
logger_config = LoggerConfig(
    enable_sentry=False  # or check environment variable
)

# Or use a different DSN for development
dev_sentry_config = SentryConfig(
    dsn=os.getenv("SENTRY_DEV_DSN"),
    environment="development",
    min_level=logging.WARNING  # Send more logs in dev
)
```

### Production Environment

```python
# Production configuration
prod_sentry_config = SentryConfig(
    dsn=os.getenv("SENTRY_DSN"),
    environment="production",
    min_level=logging.ERROR,
    traces_sample_rate=0.1,  # 10% performance monitoring
    send_default_pii=False,  # Be careful with PII in production
    default_tags={
        "service": "my-service",
        "version": os.getenv("APP_VERSION", "unknown")
    }
)
```

## Railway Deployment

The Sentry integration works seamlessly with Railway deployments:

```python
import os
from structured_logger import get_logger, LoggerConfig, SentryConfig

# Detect Railway environment
is_railway = bool(os.getenv("RAILWAY_ENVIRONMENT"))

sentry_config = SentryConfig(
    dsn=os.getenv("SENTRY_DSN"),
    environment="production" if is_railway else "development",
    release=os.getenv("RAILWAY_GIT_COMMIT_SHA", "unknown")
)

logger_config = LoggerConfig(
    enable_sentry=is_railway,  # Only enable in Railway
    sentry_config=sentry_config
)

logger = get_logger("railway_app", config=logger_config)
```

## Troubleshooting

### Check Sentry Availability

```python
from structured_logger import is_sentry_available, is_sentry_initialized

print(f"Sentry SDK available: {is_sentry_available()}")
print(f"Sentry initialized: {is_sentry_initialized()}")
```

### Debug Sentry Configuration

```python
import sentry_sdk

# Check current Sentry configuration
client = sentry_sdk.Hub.current.client
if client:
    print(f"Sentry DSN: {client.dsn}")
    print(f"Environment: {client.options.get('environment')}")
    print(f"Release: {client.options.get('release')}")
```

### Common Issues

1. **Sentry events not appearing**: Check DSN configuration and network connectivity
2. **Too many events**: Adjust `min_level` or add sampling
3. **Missing context**: Ensure `tag_fields` and `extra_fields` are configured correctly
4. **Performance issues**: Enable async logging or adjust `traces_sample_rate`

## Best Practices

1. **Use environment variables** for sensitive configuration like DSN
2. **Set appropriate log levels** to avoid spam (ERROR and above recommended)
3. **Include relevant context** in log extra fields
4. **Use breadcrumbs** to provide debugging context
5. **Set user context** early in request lifecycle
6. **Monitor Sentry quota** usage in production
7. **Test Sentry integration** in staging environment first

## API Reference

### Functions

- `initialize_sentry(config)` - Initialize Sentry SDK independently
- `capture_exception_with_context(exception, **context)` - Capture exception with context
- `capture_message_with_context(message, level, **context)` - Capture message with context
- `set_sentry_user(**user_data)` - Set user context
- `set_sentry_context(name, context)` - Set custom context
- `add_sentry_breadcrumb(message, category, level, data)` - Add debugging breadcrumb
- `is_sentry_available()` - Check if Sentry SDK is available
- `is_sentry_initialized()` - Check if Sentry is initialized

### Classes

- `SentryConfig` - Configuration for Sentry integration
- `SentryLogHandler` - Log handler that sends logs to Sentry

For more examples, see the `examples/sentry_integration_example.py` file.
