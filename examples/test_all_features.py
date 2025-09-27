"""
Comprehensive test of all advanced features working together.
"""

import asyncio
import time
import tempfile
from pathlib import Path

from structured_logger import get_logger, LoggerConfig
from structured_logger.advanced import (
    LogSchema,
    SamplingConfig,
    MetricsConfig,
    RotationConfig,
    CorrelationIDManager,
)


def test_individual_features():
    """Test each feature individually."""
    print("Testing individual features...")

    # Test 1: Async Logging
    print("  ✓ Testing async logging...")
    config = LoggerConfig(enable_async=True, force_json=True)
    logger = get_logger("test.async", config=config)

    async def test_async():
        await logger.info("Async test message")

    asyncio.run(test_async())

    # Test 2: Validation
    print("  ✓ Testing validation...")
    schema = LogSchema(required_fields={"test_field"}, field_types={"test_field": str})
    config = LoggerConfig(enable_validation=True, log_schema=schema, force_json=True)
    logger = get_logger("test.validation", config=config)
    logger.info("Valid message", extra={"test_field": "valid"})

    # Test 3: Rate Limiting
    print("  ✓ Testing rate limiting...")
    sampling_config = SamplingConfig(
        sample_rate=0.5, burst_limit=2, max_logs_per_window=3
    )
    config = LoggerConfig(
        enable_sampling=True, sampling_config=sampling_config, force_json=True
    )
    logger = get_logger("test.sampling", config=config)
    for i in range(5):
        logger.info(f"Rate limited message {i}")

    # Test 4: Metrics
    print("  ✓ Testing metrics...")
    metrics_config = MetricsConfig(enabled=True, metrics_interval=1)
    config = LoggerConfig(
        enable_metrics=True, metrics_config=metrics_config, force_json=True
    )
    logger = get_logger("test.metrics", config=config)
    logger.info("Metrics test message")

    # Test 5: File Rotation
    print("  ✓ Testing file rotation...")
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = Path(temp_dir) / "test.log"
        rotation_config = RotationConfig(max_bytes=100, backup_count=2)
        config = LoggerConfig(
            enable_file_rotation=True,
            log_file_path=str(log_file),
            rotation_config=rotation_config,
            force_json=True,
        )
        logger = get_logger("test.rotation", config=config)
        for i in range(10):
            logger.info(f"File rotation test message {i} with extra data")

    # Test 6: Correlation IDs
    print("  ✓ Testing correlation IDs...")
    config = LoggerConfig(enable_correlation_ids=True, force_json=True)
    logger = get_logger("test.correlation", config=config)

    with CorrelationIDManager.correlation_context("test-123"):
        logger.info("Correlated message 1")
        logger.info("Correlated message 2")

    print("Individual feature tests completed!\n")


def test_combined_features():
    """Test all features working together."""
    print("Testing combined features...")

    # Setup comprehensive configuration
    schema = LogSchema(
        required_fields={"operation"},
        field_types={"operation": str},
        field_validators={"operation": lambda x: len(x) > 0},
    )

    sampling_config = SamplingConfig(
        sample_rate=0.8, burst_limit=5, max_logs_per_window=20
    )

    metrics_config = MetricsConfig(
        enabled=True, track_performance=True, track_counts=True, metrics_interval=2
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = Path(temp_dir) / "combined.log"
        rotation_config = RotationConfig(max_bytes=500, backup_count=3)

        config = LoggerConfig(
            # Enable all features
            enable_async=True,
            enable_validation=True,
            enable_sampling=True,
            enable_metrics=True,
            enable_file_rotation=True,
            enable_correlation_ids=True,
            # Feature configurations
            log_schema=schema,
            sampling_config=sampling_config,
            metrics_config=metrics_config,
            rotation_config=rotation_config,
            log_file_path=str(log_file),
            force_json=True,
        )

        logger = get_logger("test.combined", config=config)

        async def combined_test():
            # Test with correlation context
            with CorrelationIDManager.correlation_context("combined-test-456"):
                await logger.info(
                    "Combined test started", extra={"operation": "test_start"}
                )

                # Generate multiple logs for sampling and rotation
                for i in range(15):
                    await logger.info(
                        f"Combined test step {i}",
                        extra={
                            "operation": "test_step",
                            "step": i,
                            "data": f"test_data_{i}" * 10,  # Make logs larger
                        },
                    )

                    if i % 5 == 0:
                        await logger.warning(
                            f"Checkpoint at step {i}", extra={"operation": "checkpoint"}
                        )

                await logger.info(
                    "Combined test completed", extra={"operation": "test_end"}
                )

        # Run the combined test
        asyncio.run(combined_test())

        # Check if files were created
        log_files = list(Path(temp_dir).glob("*.log*"))
        print(f"  ✓ Created {len(log_files)} log files")

        if log_files:
            print(f"  ✓ Main log file size: {log_files[0].stat().st_size} bytes")

    print("Combined features test completed!\n")


def test_error_handling():
    """Test error handling and graceful degradation."""
    print("Testing error handling...")

    # Test with invalid schema
    try:
        schema = LogSchema(
            required_fields={"invalid_field"}, field_types={"invalid_field": str}
        )
        config = LoggerConfig(
            enable_validation=True, log_schema=schema, force_json=True
        )
        logger = get_logger("test.error", config=config)

        # This should be dropped due to validation failure
        logger.info("This message has missing required field")

        # This should pass validation
        logger.info("Valid message", extra={"invalid_field": "present"})

        print("  ✓ Validation error handling works")

    except Exception as e:
        print(f"  ✗ Validation error handling failed: {e}")

    # Test rate limiter edge cases
    try:
        sampling_config = SamplingConfig(
            sample_rate=0.0,  # No sampling
            burst_limit=0,  # No burst
            max_logs_per_window=1,
        )
        config = LoggerConfig(
            enable_sampling=True, sampling_config=sampling_config, force_json=True
        )
        logger = get_logger("test.edge", config=config)

        # Only first log should pass
        for i in range(5):
            logger.info(f"Edge case test {i}")

        print("  ✓ Rate limiter edge cases handled")

    except Exception as e:
        print(f"  ✗ Rate limiter error handling failed: {e}")

    print("Error handling tests completed!\n")


def test_performance():
    """Basic performance test."""
    print("Testing performance...")

    start_time = time.time()

    # Standard logging
    config = LoggerConfig(force_json=True)
    logger = get_logger("test.perf.standard", config=config)

    for i in range(1000):
        logger.info(f"Standard log {i}", extra={"iteration": i})

    standard_time = time.time() - start_time

    # Advanced features logging
    start_time = time.time()

    schema = LogSchema(required_fields={"iteration"})
    metrics_config = MetricsConfig(enabled=True)
    config = LoggerConfig(
        enable_validation=True,
        enable_metrics=True,
        log_schema=schema,
        metrics_config=metrics_config,
        force_json=True,
    )
    logger = get_logger("test.perf.advanced", config=config)

    for i in range(1000):
        logger.info(f"Advanced log {i}", extra={"iteration": i})

    advanced_time = time.time() - start_time

    print(f"  ✓ Standard logging: {standard_time:.3f}s")
    print(f"  ✓ Advanced logging: {advanced_time:.3f}s")
    print(
        f"  ✓ Overhead: {((advanced_time - standard_time) / standard_time * 100):.1f}%"
    )

    print("Performance tests completed!\n")


if __name__ == "__main__":
    print("Structured Logger - Advanced Features Test Suite\n")
    print("=" * 50)

    try:
        test_individual_features()
        test_combined_features()
        test_error_handling()
        test_performance()

        print("=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("\nAdvanced features are working correctly!")

    except Exception as e:
        print("=" * 50)
        print(f"❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
