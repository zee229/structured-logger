# Advanced Features

This document describes the advanced features available in structured-logger v1.1.0+.

## Overview

The advanced features module provides enterprise-grade logging capabilities including:

- **Async Logging** - High-performance non-blocking logging
- **Log Validation** - Schema-based validation of log entries
- **Rate Limiting & Sampling** - Prevent log flooding and control volume
- **Metrics Collection** - Built-in performance and usage metrics
- **File Rotation** - Automatic log file management
- **Correlation IDs** - Request tracing and correlation

## Installation

All advanced features are included in the base package with no additional dependencies required.

```python
from structured_logger import get_logger, LoggerConfig
from structured_logger.advanced import (
    LogSchema, SamplingConfig, MetricsConfig, RotationConfig,
    CorrelationIDManager
)
```

## Async Logging

High-performance async logging for applications that need non-blocking log operations.

### Configuration

```python
config = LoggerConfig(
    enable_async=True,
    force_json=True
)

logger = get_logger(__name__, config=config)
```

### Usage

```python
import asyncio

async def my_async_function():
    await logger.info("Async log message", extra={"user_id": "123"})
    await logger.error("Async error", extra={"error_code": "E001"})

# Run async code
asyncio.run(my_async_function())
```

### Benefits

- Non-blocking log operations
- Better performance for high-throughput applications
- Automatic queue management
- Thread-safe operation

## Log Validation

Enforce schema validation on log entries to ensure consistency and data quality.

### Schema Definition

```python
from structured_logger.advanced import LogSchema

schema = LogSchema(
    required_fields={"user_id", "action"},
    optional_fields={"session_id", "ip_address"},
    field_types={
        "user_id": str,
        "action": str,
        "session_id": str
    },
    field_validators={
        "user_id": lambda x: len(x) > 0,
        "action": lambda x: x in ["login", "logout", "view", "edit"]
    },
    max_message_length=500,
    allowed_levels={"INFO", "WARNING", "ERROR"}
)
```

### Configuration

```python
config = LoggerConfig(
    enable_validation=True,
    log_schema=schema,
    force_json=True
)

logger = get_logger(__name__, config=config)
```

### Behavior

- Invalid log entries are dropped silently
- Validation errors don't crash the application
- Configurable validation rules per field
- Type checking and custom validators

## Rate Limiting & Sampling

Control log volume and prevent flooding with configurable rate limiting and sampling.

### Configuration

```python
from structured_logger.advanced import SamplingConfig

sampling_config = SamplingConfig(
    sample_rate=0.1,          # Sample 10% of logs
    burst_limit=100,          # Allow 100 logs before sampling
    time_window=60,           # 60-second time window
    max_logs_per_window=1000  # Max 1000 logs per window
)

config = LoggerConfig(
    enable_sampling=True,
    sampling_config=sampling_config
)
```

### How It Works

1. **Burst Allowance**: First N logs are always allowed
2. **Time Windows**: Rate limiting applied per time window
3. **Sampling**: After limits, only sample_rate % of logs are kept
4. **Automatic Cleanup**: Old timestamps are automatically cleaned

## Metrics Collection

Built-in metrics collection for monitoring logging performance and usage patterns.

### Configuration

```python
from structured_logger.advanced import MetricsConfig

metrics_config = MetricsConfig(
    enabled=True,
    track_performance=True,
    track_counts=True,
    track_errors=True,
    metrics_interval=60  # Report every 60 seconds
)

config = LoggerConfig(
    enable_metrics=True,
    metrics_config=metrics_config
)
```

### Collected Metrics

- **Log Counts**: Count by log level
- **Performance**: Processing time statistics
- **Error Tracking**: Error counts by location
- **Uptime**: Application uptime tracking

### Accessing Metrics

Metrics are automatically logged to the `structured_logger.metrics` logger:

```json
{
  "time": "2024-01-15 10:30:45,123",
  "level": "INFO",
  "message": "Logging metrics",
  "module": "structured_logger.metrics",
  "metrics": {
    "uptime": 3600.5,
    "counts": {
      "INFO": 150,
      "ERROR": 5,
      "total": 155
    },
    "performance": {
      "INFO": {"avg": 0.002, "min": 0.001, "max": 0.010},
      "ERROR": {"avg": 0.005, "min": 0.003, "max": 0.015}
    },
    "errors": {
      "myapp:process_data": 3,
      "myapp:validate_input": 2
    }
  }
}
```

## File Rotation

Automatic log file management with size-based or time-based rotation.

### Size-Based Rotation

```python
from structured_logger.advanced import RotationConfig

rotation_config = RotationConfig(
    max_bytes=10 * 1024 * 1024,  # 10MB
    backup_count=5,
    rotation_type="size",
    encoding="utf-8"
)

config = LoggerConfig(
    enable_file_rotation=True,
    log_file_path="/var/log/app.log",
    rotation_config=rotation_config
)
```

### Time-Based Rotation

```python
rotation_config = RotationConfig(
    rotation_type="time",
    when="midnight",  # Rotate at midnight
    interval=1,       # Every day
    backup_count=7    # Keep 7 days
)
```

### Features

- Automatic file rotation
- Configurable backup retention
- Multiple rotation strategies
- Compression support (planned)

## Correlation IDs

Automatic request/trace correlation for distributed systems and request tracking.

### Basic Usage

```python
from structured_logger.advanced import CorrelationIDManager

config = LoggerConfig(
    enable_correlation_ids=True,
    force_json=True
)

logger = get_logger(__name__, config=config)

# Manual correlation ID
with CorrelationIDManager.correlation_context("my-request-123"):
    logger.info("Processing started")
    logger.info("Step 1 completed")
    logger.info("Processing finished")

# Auto-generated correlation ID
with CorrelationIDManager.correlation_context() as correlation_id:
    logger.info("Auto-correlated log", extra={"correlation_id": correlation_id})
```

### Web Framework Integration

#### Flask

```python
from flask import Flask, g
import uuid

@app.before_request
def before_request():
    g.request_id = str(uuid.uuid4())
    CorrelationIDManager.set_correlation_id(g.request_id)

@app.after_request
def after_request(response):
    CorrelationIDManager.clear_correlation_id()
    return response
```

#### FastAPI

```python
from fastapi import Request
import uuid

@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    correlation_id = str(uuid.uuid4())
    CorrelationIDManager.set_correlation_id(correlation_id)

    try:
        response = await call_next(request)
        return response
    finally:
        CorrelationIDManager.clear_correlation_id()
```

## Combined Configuration

You can enable multiple advanced features together:

```python
config = LoggerConfig(
    # Basic settings
    force_json=True,

    # Advanced features
    enable_async=True,
    enable_validation=True,
    enable_sampling=True,
    enable_metrics=True,
    enable_file_rotation=True,
    enable_correlation_ids=True,

    # Feature configurations
    log_schema=my_schema,
    sampling_config=my_sampling_config,
    metrics_config=my_metrics_config,
    rotation_config=my_rotation_config,
    log_file_path="/var/log/app.log"
)

logger = get_logger(__name__, config=config)
```

## Performance Considerations

### Async Logging
- Minimal overhead for async operations
- Queue-based buffering prevents blocking
- Automatic overflow handling

### Validation
- Schema validation adds ~0.1-0.5ms per log
- Failed validations are fast (early termination)
- Minimal memory overhead

### Rate Limiting
- Efficient timestamp tracking with deque
- Automatic cleanup of old data
- O(1) operations for most cases

### Metrics
- Background thread for metrics reporting
- Minimal impact on logging performance
- Configurable reporting intervals

### File Rotation
- Standard Python logging rotation
- Efficient file handling
- Configurable retention policies

## Error Handling

All advanced features are designed to fail gracefully:

- Invalid configurations use safe defaults
- Feature errors don't crash the application
- Graceful degradation when features are unavailable
- Comprehensive error logging (to separate logger)

## Examples

See the `examples/` directory for complete working examples:

- `advanced_features.py` - Demonstrates all features
- `flask_advanced.py` - Flask integration
- `fastapi_advanced.py` - FastAPI integration

## Migration Guide

Existing code continues to work without changes. To enable advanced features:

1. Update configuration to enable desired features
2. Add feature-specific configuration objects
3. Update imports to include advanced classes
4. Test thoroughly in development environment

## Troubleshooting

### Advanced Features Not Available

If you get import errors for advanced features:

1. Ensure you're using version 1.1.0+
2. Check that the `advanced.py` module exists
3. Verify no import conflicts

### Performance Issues

If logging performance degrades:

1. Disable validation for high-volume logs
2. Adjust sampling rates
3. Consider async logging for better throughput
4. Monitor metrics for bottlenecks

### Memory Usage

For high-volume applications:

1. Configure appropriate rate limiting
2. Set reasonable metrics intervals
3. Use file rotation to manage disk space
4. Monitor queue sizes for async logging