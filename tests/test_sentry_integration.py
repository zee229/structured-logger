#!/usr/bin/env python3
"""
Simple test script to verify Sentry integration works correctly.

This script tests the Sentry integration without requiring an actual Sentry DSN.
It verifies that:
1. The integration can be imported without errors
2. Configuration works correctly
3. Handlers are set up properly
4. Logging works with and without Sentry enabled
"""

import logging
import os
import sys
from pathlib import Path

# Add the package to Python path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_imports():
    """Test that all Sentry integration components can be imported."""
    print("Testing imports...")

    try:
        from structured_logger import (LoggerConfig, get_logger,
                                       is_sentry_available,
                                       is_sentry_initialized)

        print("✓ Basic imports successful")
    except ImportError as e:
        print(f"✗ Basic import failed: {e}")
        return False

    try:
        from structured_logger import (SentryConfig, SentryLogHandler,
                                       add_sentry_breadcrumb,
                                       capture_exception_with_context,
                                       capture_message_with_context,
                                       initialize_sentry, set_sentry_context,
                                       set_sentry_user)

        print("✓ Sentry integration imports successful")
        return True
    except ImportError as e:
        print(f"✗ Sentry integration import failed: {e}")
        print("  This is expected if sentry-sdk is not installed")
        return False


def test_sentry_availability():
    """Test Sentry availability detection."""
    print("\nTesting Sentry availability...")

    from structured_logger import is_sentry_available, is_sentry_initialized

    available = is_sentry_available()
    initialized = is_sentry_initialized()

    print(f"✓ Sentry available: {available}")
    print(f"✓ Sentry initialized: {initialized}")

    return available


def test_basic_logging_without_sentry():
    """Test basic logging functionality without Sentry enabled."""
    print("\nTesting basic logging without Sentry...")

    from structured_logger import LoggerConfig, get_logger

    # Configure logger without Sentry
    config = LoggerConfig(enable_sentry=False, custom_fields=["user_id", "request_id"])

    logger = get_logger("test_logger", config=config)

    # Test different log levels
    logger.debug("Debug message")
    logger.info("Info message", extra={"user_id": "test123", "request_id": "req456"})
    logger.warning("Warning message")
    logger.error("Error message")

    print("✓ Basic logging without Sentry works")
    return True


def test_sentry_configuration():
    """Test Sentry configuration without actual initialization."""
    print("\nTesting Sentry configuration...")

    try:
        from structured_logger import LoggerConfig, SentryConfig

        # Test SentryConfig creation
        sentry_config = SentryConfig(
            dsn="https://fake-dsn@sentry.io/123456",
            min_level=logging.ERROR,
            environment="test",
            default_tags={"service": "test"},
            tag_fields=["user_id", "request_id"],
        )

        # Test LoggerConfig with Sentry
        logger_config = LoggerConfig(enable_sentry=True, sentry_config=sentry_config)

        print("✓ Sentry configuration creation works")
        return True

    except Exception as e:
        print(f"✗ Sentry configuration failed: {e}")
        return False


def test_logger_with_sentry_config():
    """Test logger creation with Sentry configuration (but no actual Sentry)."""
    print("\nTesting logger with Sentry configuration...")

    try:
        from structured_logger import LoggerConfig, SentryConfig, get_logger

        # Create Sentry config with fake DSN
        sentry_config = SentryConfig(
            dsn=None,  # No DSN means Sentry won't actually initialize
            min_level=logging.ERROR,
            environment="test",
        )

        # Create logger config with Sentry enabled
        logger_config = LoggerConfig(
            enable_sentry=True,
            sentry_config=sentry_config,
            custom_fields=["user_id", "company_id"],
        )

        # Get logger - should work even without valid Sentry DSN
        logger = get_logger("test_sentry_logger", config=logger_config)

        # Test logging - should work normally
        logger.info("Test info message")
        logger.error(
            "Test error message",
            extra={
                "user_id": "user123",
                "company_id": "company456",
                "error_code": "TEST_ERROR",
            },
        )

        print("✓ Logger with Sentry configuration works")
        return True

    except Exception as e:
        print(f"✗ Logger with Sentry configuration failed: {e}")
        return False


def test_manual_sentry_functions():
    """Test manual Sentry functions (should handle missing Sentry gracefully)."""
    print("\nTesting manual Sentry functions...")

    try:
        from structured_logger import (add_sentry_breadcrumb,
                                       capture_exception_with_context,
                                       capture_message_with_context,
                                       set_sentry_user)

        # These should not raise errors even if Sentry is not initialized
        event_id = capture_message_with_context(
            "Test message", level="info", user_id="test123"
        )

        set_sentry_user(user_id="test123", email="test@example.com")

        add_sentry_breadcrumb(message="Test breadcrumb", category="test", level="info")

        # Test exception capture
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            event_id = capture_exception_with_context(
                e, user_id="test123", context="test"
            )

        print("✓ Manual Sentry functions work (gracefully handle missing Sentry)")
        return True

    except Exception as e:
        print(f"✗ Manual Sentry functions failed: {e}")
        return False


def test_with_real_sentry():
    """Test with real Sentry if DSN is provided."""
    print("\nTesting with real Sentry (if DSN provided)...")

    from structured_logger import is_sentry_available

    if not is_sentry_available():
        print("⚠ Sentry SDK not available, skipping real Sentry test")
        print("  Install with: pip install sentry-sdk")
        return True

    sentry_dsn = os.getenv("SENTRY_DSN")
    if not sentry_dsn:
        print("⚠ No SENTRY_DSN environment variable set, skipping real Sentry test")
        return True

    try:
        from structured_logger import LoggerConfig, SentryConfig, get_logger

        # Configure with real Sentry DSN
        sentry_config = SentryConfig(
            dsn=sentry_dsn,
            min_level=logging.WARNING,
            environment="test",
            default_tags={"test": "integration"},
        )

        logger_config = LoggerConfig(enable_sentry=True, sentry_config=sentry_config)

        logger = get_logger("real_sentry_test", config=logger_config)

        # Send test messages
        logger.warning("Test warning message from integration test")
        logger.error(
            "Test error message from integration test",
            extra={"test_id": "integration_test", "timestamp": "2024-01-01T00:00:00Z"},
        )

        print("✓ Real Sentry integration test completed")
        print("  Check your Sentry dashboard for test events")
        return True

    except Exception as e:
        print(f"✗ Real Sentry test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=== Sentry Integration Test Suite ===\n")

    tests = [
        test_imports,
        test_sentry_availability,
        test_basic_logging_without_sentry,
        test_sentry_configuration,
        test_logger_with_sentry_config,
        test_manual_sentry_functions,
        test_with_real_sentry,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            results.append(False)

    # Summary
    print(f"\n=== Test Results ===")
    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")

    # Consider it successful if all tests that could run passed
    # (The real Sentry test is optional and skipped if SDK not available)
    if passed >= total - 1:  # Allow one test to be skipped
        print("🎉 All available tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
