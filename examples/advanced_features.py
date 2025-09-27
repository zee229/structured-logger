"""
Advanced features examples for structured-logger.

Demonstrates async logging, validation, rate limiting, metrics,
file rotation, and correlation IDs.
"""

import asyncio
import time
from pathlib import Path

from structured_logger import LoggerConfig, get_logger
from structured_logger.advanced import (
    CorrelationIDManager,
    LogSchema,
    MetricsConfig,
    RotationConfig,
    SamplingConfig,
)


def example_async_logging():
    """Example of async logging for high-performance applications."""
    print("=== Async Logging Example ===")

    config = LoggerConfig(enable_async=True, force_json=True)

    logger = get_logger(__name__ + ".async", config=config)

    async def async_task():
        for i in range(5):
            await logger.info(f"Async log message {i}", extra={"task_id": f"task_{i}"})
            await asyncio.sleep(0.1)

    # Run async logging
    asyncio.run(async_task())
    print("Async logging completed")


def example_log_validation():
    """Example of log validation with schema enforcement."""
    print("=== Log Validation Example ===")

    # Define schema
    schema = LogSchema(
        required_fields={"user_id", "action"},
        field_types={"user_id": str, "action": str},
        max_message_length=100,
        field_validators={
            "user_id": lambda x: len(x) > 0,
            "action": lambda x: x in ["login", "logout", "view", "edit"],
        },
    )

    config = LoggerConfig(enable_validation=True, log_schema=schema, force_json=True)

    logger = get_logger(__name__ + ".validation", config=config)

    # Valid log
    logger.info("User action", extra={"user_id": "123", "action": "login"})

    # Invalid log (missing required field) - will be dropped
    logger.info("Invalid action", extra={"user_id": "123"})

    # Invalid log (bad action) - will be dropped
    logger.info("Bad action", extra={"user_id": "123", "action": "invalid"})

    print("Validation example completed")


def example_rate_limiting():
    """Example of rate limiting and sampling."""
    print("=== Rate Limiting Example ===")

    sampling_config = SamplingConfig(
        sample_rate=0.5,  # Sample 50% of logs
        burst_limit=3,  # Allow 3 logs before sampling
        time_window=10,  # 10 second window
        max_logs_per_window=5,  # Max 5 logs per window
    )

    config = LoggerConfig(
        enable_sampling=True, sampling_config=sampling_config, force_json=True
    )

    logger = get_logger(__name__ + ".sampling", config=config)

    # Generate many logs quickly
    for i in range(10):
        logger.info(f"Rate limited log {i}", extra={"iteration": i})
        time.sleep(0.1)

    print("Rate limiting example completed")


def example_metrics_collection():
    """Example of metrics collection."""
    print("=== Metrics Collection Example ===")

    metrics_config = MetricsConfig(
        enabled=True,
        track_performance=True,
        track_counts=True,
        track_errors=True,
        metrics_interval=5,  # Report every 5 seconds
    )

    config = LoggerConfig(
        enable_metrics=True, metrics_config=metrics_config, force_json=True
    )

    logger = get_logger(__name__ + ".metrics", config=config)

    # Generate various log levels
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")

    # Wait a bit for metrics to be collected
    time.sleep(2)
    print("Metrics collection example completed")


def example_file_rotation():
    """Example of file-based logging with rotation."""
    print("=== File Rotation Example ===")

    log_file = Path("logs/app.log")
    log_file.parent.mkdir(exist_ok=True)

    rotation_config = RotationConfig(
        max_bytes=1024, backup_count=3, rotation_type="size"  # Small size for demo
    )

    config = LoggerConfig(
        enable_file_rotation=True,
        log_file_path=str(log_file),
        rotation_config=rotation_config,
        force_json=True,
    )

    logger = get_logger(__name__ + ".rotation", config=config)

    # Generate enough logs to trigger rotation
    for i in range(20):
        logger.info(f"File rotation test log {i}", extra={"data": "x" * 50})
    print(f"File rotation example completed. Check {log_file.parent}")


def example_correlation_ids():
    """Example of correlation ID usage."""
    print("=== Correlation IDs Example ===")

    config = LoggerConfig(enable_correlation_ids=True, force_json=True)

    logger = get_logger(__name__ + ".correlation", config=config)

    # Manual correlation ID
    with CorrelationIDManager.correlation_context("manual-123") as correlation_id:
        logger.info("Request started", extra={"operation": "user_login"})
        logger.info("Processing step 1")
        logger.info("Processing step 2")
        logger.info("Request completed")

    # Auto-generated correlation ID
    with CorrelationIDManager.correlation_context() as correlation_id:
        logger.info(
            "Auto-generated correlation", extra={"correlation_id": correlation_id}
        )

        print("Correlation IDs example completed")


def example_combined_features():
    """Example combining multiple advanced features."""
    print("=== Combined Features Example ===")

    # Setup comprehensive configuration
    schema = LogSchema(required_fields={"request_id"}, field_types={"request_id": str})

    sampling_config = SamplingConfig(sample_rate=0.8)
    metrics_config = MetricsConfig(enabled=True)

    config = LoggerConfig(
        enable_async=True,
        enable_validation=True,
        enable_sampling=True,
        enable_metrics=True,
        enable_correlation_ids=True,
        log_schema=schema,
        sampling_config=sampling_config,
        metrics_config=metrics_config,
        force_json=True,
    )

    logger = get_logger(__name__ + ".combined", config=config)

    async def complex_operation():
        with CorrelationIDManager.correlation_context() as correlation_id:
            for i in range(5):
                await logger.info(
                    f"Complex operation step {i}",
                    extra={
                        "request_id": f"req_{i}",
                        "step": i,
                        "operation": "complex_task",
                    },
                )
                await asyncio.sleep(0.1)

    asyncio.run(complex_operation())
    print("Combined features example completed")


if __name__ == "__main__":
    print("Structured Logger - Advanced Features Examples")

    # Run all examples
    example_async_logging()
    example_log_validation()
    example_rate_limiting()
    example_metrics_collection()
    example_file_rotation()
    example_correlation_ids()
    example_combined_features()

    print("All advanced features examples completed!")
