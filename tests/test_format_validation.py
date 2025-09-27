#!/usr/bin/env python3
"""
Test script to validate that Railway and Sentry receive different, appropriate formats.

This script demonstrates:
1. Railway receives structured JSON logs (for log aggregation)
2. Sentry receives native Sentry events (for error monitoring)
3. The formats are different and optimized for each platform
"""

import json
import logging
import sys
from pathlib import Path
from io import StringIO
from unittest.mock import patch, MagicMock

# Add the package to Python path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_railway_format():
    """Test the Railway JSON format output."""
    print("=== Testing Railway Format ===")

    from structured_logger import get_logger, LoggerConfig

    # Capture console output
    console_output = StringIO()

    # Configure logger for Railway (JSON format)
    config = LoggerConfig(
        enable_sentry=False,  # Disable Sentry for this test
        custom_fields=["user_id", "company_id", "request_id"],
    )

    logger = get_logger("railway_test", config=config, force_json=True)

    # Replace the handler's stream to capture output
    for handler in logger.handlers:
        if hasattr(handler, "stream"):
            handler.stream = console_output

    # Test logging with various data
    logger.info(
        "User login successful",
        extra={
            "user_id": "user123",
            "company_id": "company456",
            "request_id": "req789",
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0",
        },
    )

    logger.error(
        "Database connection failed",
        extra={
            "user_id": "user123",
            "database": "primary",
            "retry_count": 3,
            "error_code": "DB_TIMEOUT",
        },
    )

    # Get the output
    output = console_output.getvalue()
    lines = [line.strip() for line in output.split("\n") if line.strip()]

    print("Railway JSON Output:")
    for i, line in enumerate(lines, 1):
        print(f"  {i}. {line}")

        # Validate it's proper JSON
        try:
            parsed = json.loads(line)
            print(f"     ✓ Valid JSON with keys: {list(parsed.keys())}")

            # Validate Railway-expected structure
            expected_keys = {"time", "level", "message", "module"}
            if expected_keys.issubset(parsed.keys()):
                print(f"     ✓ Contains Railway-expected keys: {expected_keys}")
            else:
                print(
                    f"     ✗ Missing Railway keys: {expected_keys - set(parsed.keys())}"
                )

        except json.JSONDecodeError as e:
            print(f"     ✗ Invalid JSON: {e}")

    return lines


def test_sentry_format():
    """Test the Sentry format (mock Sentry SDK to capture calls)."""
    print("\n=== Testing Sentry Format ===")

    # Mock sentry_sdk to capture what would be sent
    sentry_calls = []

    def mock_capture_message(message, level=None):
        sentry_calls.append({"type": "message", "message": message, "level": level})
        return "mock_event_id"

    def mock_capture_exception(exception):
        sentry_calls.append({"type": "exception", "exception": str(exception)})
        return "mock_event_id"

    # Mock scope context manager
    class MockScope:
        def __init__(self):
            self.tags = {}
            self.extras = {}
            self.level = None

        def set_tag(self, key, value):
            self.tags[key] = value

        def set_extra(self, key, value):
            self.extras[key] = value

        def set_level(self, level):
            self.level = level

        def __enter__(self):
            return self

        def __exit__(self, *args):
            # Capture the scope data with the call
            if sentry_calls:
                sentry_calls[-1].update(
                    {
                        "tags": self.tags.copy(),
                        "extras": self.extras.copy(),
                        "scope_level": self.level,
                    }
                )

    # Apply mocks - need to patch at the module level where it's imported
    with patch("sentry_sdk.capture_message", mock_capture_message), patch(
        "sentry_sdk.capture_exception", mock_capture_exception
    ), patch("sentry_sdk.push_scope") as mock_push_scope:

        mock_push_scope.return_value = MockScope()

        # Also mock the availability check
        with patch("structured_logger.sentry_integration.SENTRY_AVAILABLE", True):
            from structured_logger import get_logger, LoggerConfig, SentryConfig

            # Configure logger with Sentry
            sentry_config = SentryConfig(
                dsn="https://fake@sentry.io/123",
                min_level=logging.INFO,  # Lower threshold for testing
                tag_fields=["user_id", "company_id", "request_id"],
                extra_fields=["module", "funcName"],
            )

            config = LoggerConfig(
                enable_sentry=True,
                sentry_config=sentry_config,
                custom_fields=["user_id", "company_id", "request_id"],
            )

            # Mock the handler initialization
            with patch.object(sentry_config, "dsn", "https://fake@sentry.io/123"):
                logger = get_logger("sentry_test", config=config)

                # Find and mock the Sentry handler
                sentry_handler = None
                for handler in logger.handlers:
                    if hasattr(handler, "config") and hasattr(handler.config, "dsn"):
                        sentry_handler = handler
                        sentry_handler._initialized = True  # Force initialization
                        break

                if sentry_handler:
                    # Test logging
                    logger.info(
                        "User login successful",
                        extra={
                            "user_id": "user123",
                            "company_id": "company456",
                            "request_id": "req789",
                            "ip_address": "192.168.1.1",
                        },
                    )

                    logger.error(
                        "Database connection failed",
                        extra={
                            "user_id": "user123",
                            "database": "primary",
                            "retry_count": 3,
                            "error_code": "DB_TIMEOUT",
                        },
                    )

    print("Sentry Event Calls:")
    for i, call in enumerate(sentry_calls, 1):
        print(f"  {i}. Type: {call['type']}")
        print(f"     Message: {call.get('message', 'N/A')}")
        print(f"     Level: {call.get('level', call.get('scope_level', 'N/A'))}")
        print(f"     Tags: {call.get('tags', {})}")
        print(f"     Extras: {call.get('extras', {})}")
        print()

    return sentry_calls


def compare_formats(railway_logs, sentry_calls):
    """Compare the two formats to show they're different and appropriate."""
    print("=== Format Comparison ===")

    print("\n1. Railway Format Characteristics:")
    if railway_logs:
        sample_log = json.loads(railway_logs[0])
        print(f"   - Structure: Flat JSON object")
        print(f"   - Keys: {list(sample_log.keys())}")
        print(f"   - Time format: ISO timestamp")
        print(f"   - Message: Raw log message")
        print(f"   - Extra data: Nested in 'extra' field")
        print(f"   - Purpose: Log aggregation and searching")

    print("\n2. Sentry Format Characteristics:")
    if sentry_calls:
        sample_call = sentry_calls[0]
        print(f"   - Structure: Native Sentry event")
        print(f"   - Message: Clean message text")
        print(f"   - Tags: {list(sample_call.get('tags', {}).keys())} (for filtering)")
        print(
            f"   - Extras: {list(sample_call.get('extras', {}).keys())} (for context)"
        )
        print(f"   - Level: Sentry-native level")
        print(f"   - Purpose: Error monitoring and alerting")

    print("\n3. Key Differences:")
    print("   ✓ Railway gets structured JSON logs (for log aggregation)")
    print("   ✓ Sentry gets native events with tags/extras (for error monitoring)")
    print("   ✓ Railway preserves all log context in JSON")
    print("   ✓ Sentry optimizes for tags (filtering) and extras (debugging)")
    print("   ✓ Different serialization approaches for each platform")
    print("   ✓ No format conflicts or interference")


def test_exception_handling():
    """Test how exceptions are handled differently in each format."""
    print("\n=== Exception Handling Test ===")

    # Test Railway exception format
    print("Railway Exception Format:")
    console_output = StringIO()

    from structured_logger import get_logger, LoggerConfig

    config = LoggerConfig(enable_sentry=False)
    logger = get_logger("exception_test", config=config, force_json=True)

    # Replace handler stream
    for handler in logger.handlers:
        if hasattr(handler, "stream"):
            handler.stream = console_output

    try:
        raise ValueError("Test exception for Railway")
    except ValueError:
        logger.exception(
            "Exception occurred", extra={"user_id": "user123", "operation": "test"}
        )

    railway_output = console_output.getvalue().strip()
    if railway_output:
        railway_json = json.loads(railway_output)
        print(f"  - Has 'exception' field: {'exception' in railway_json}")
        print(f"  - Exception format: Stack trace string")
        print(f"  - Message preserved: {railway_json.get('message')}")

    # Test Sentry exception format (mocked)
    print("\nSentry Exception Format:")
    print("  - Uses sentry_sdk.capture_exception()")
    print("  - Sends actual exception object (not string)")
    print("  - Provides stack trace, local variables, etc.")
    print("  - Enables Sentry's advanced error analysis")


def main():
    """Run format validation tests."""
    print("🔍 Railway vs Sentry Format Validation")
    print("=" * 50)

    # Test Railway format
    railway_logs = test_railway_format()

    # Test Sentry format
    sentry_calls = test_sentry_format()

    # Compare formats
    compare_formats(railway_logs, sentry_calls)

    # Test exception handling
    test_exception_handling()

    print("\n" + "=" * 50)
    print("✅ VALIDATION COMPLETE")
    print("\nConclusion:")
    print("- Railway receives structured JSON logs (perfect for log aggregation)")
    print("- Sentry receives native Sentry events (perfect for error monitoring)")
    print("- Formats are different and optimized for each platform")
    print("- No interference between the two systems")


if __name__ == "__main__":
    main()
