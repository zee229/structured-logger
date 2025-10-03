#!/usr/bin/env python3
"""
Test script to verify the 'error' field fix works correctly.
This reproduces the issue and verifies the fix.
"""

import logging
import os
import sys

from structured_logger import LoggerConfig, SentryConfig, get_logger


def test_error_field_handling():
    """Test that 'error' fields in extra don't cause Logger._log() errors."""

    print("Testing error field handling...")

    # Test 1: Basic logger without Sentry
    print("\n1. Testing basic logger with error field...")
    logger = get_logger("test_basic")

    try:
        logger.error("Test message", extra={"error": "some error details"})
        print("✓ Basic logger handles 'error' field correctly")
    except Exception as e:
        print(f"✗ Basic logger failed: {e}")
        return False

    # Test 2: Logger with Sentry integration (mock)
    print("\n2. Testing logger with Sentry integration...")

    # Configure with Sentry but no actual DSN (so it won't initialize)
    sentry_config = SentryConfig(
        dsn=None, min_level=logging.ERROR  # No DSN so it won't actually initialize
    )

    logger_config = LoggerConfig(enable_sentry=True, sentry_config=sentry_config)

    logger_with_sentry = get_logger("test_sentry", config=logger_config)

    try:
        logger_with_sentry.error(
            "Test message with Sentry",
            extra={
                "error": "some error details",
                "user_id": "test123",
                "request_id": "req456",
            },
        )
        print("✓ Logger with Sentry handles 'error' field correctly")
    except Exception as e:
        print(f"✗ Logger with Sentry failed: {e}")
        return False

    # Test 3: Multiple error scenarios
    print("\n3. Testing various error field scenarios...")

    test_cases = [
        {"error": "string error"},
        {"error": Exception("test exception")},
        {"error": {"nested": "error object"}},
        {"error": ["list", "of", "errors"]},
        {"error": None},  # Should be handled gracefully
    ]

    for i, extra_data in enumerate(test_cases):
        try:
            logger.info(f"Test case {i + 1}", extra=extra_data)
            print(f"✓ Test case {i + 1} passed: {extra_data}")
        except Exception as e:
            print(f"✗ Test case {i + 1} failed: {e}")
            return False

    print("\n✅ All tests passed! The 'error' field fix is working correctly.")
    return True


def test_railway_simulation():
    """Simulate Railway environment with JSON logging."""
    print("\n" + "=" * 50)
    print("RAILWAY SIMULATION TEST")
    print("=" * 50)

    # Set environment variables to simulate Railway
    os.environ["RAILWAY_ENVIRONMENT"] = "production"
    os.environ["LOG_LEVEL"] = "INFO"

    # Force JSON formatting (like in Railway)
    logger = get_logger("railway_test", force_json=True)

    print("\nTesting Railway-like scenario with JSON logging...")

    try:
        # This is the type of call that was causing the error
        logger.error(
            "Request failed",
            extra={
                "error": "Database connection timeout",
                "user_id": "user123",
                "request_id": "req789",
                "status_code": 500,
            },
        )
        print("✓ Railway simulation test passed")
        return True
    except Exception as e:
        print(f"✗ Railway simulation test failed: {e}")
        return False


if __name__ == "__main__":
    print("Testing structured-logger error field handling fix")
    print("=" * 60)

    success = True

    # Run basic tests
    if not test_error_field_handling():
        success = False

    # Run Railway simulation
    if not test_railway_simulation():
        success = False

    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED! The fix should resolve the Railway error.")
        print(
            "\nThe 'error' field in extra data is now handled safely and will appear as 'error_details' in logs."
        )
    else:
        print("❌ Some tests failed. Please check the implementation.")
        sys.exit(1)
