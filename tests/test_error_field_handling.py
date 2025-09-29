"""
Test cases for handling 'error' fields in log extra data.

This tests the fix for the issue where 'error' fields in extra data
would conflict with Python's logging internals and cause:
TypeError: Logger._log() got an unexpected keyword argument 'error'
"""

import json
import logging
from io import StringIO

from structured_logger import LoggerConfig, StructuredLogFormatter, get_logger

# import pytest  # Not needed for direct execution


try:
    from structured_logger import SentryConfig

    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False


class TestErrorFieldHandling:
    """Test handling of 'error' fields in log extra data."""

    def test_error_field_in_basic_logger(self):
        """Test that 'error' field in extra data doesn't cause conflicts."""
        # Create a logger with string output capture
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        formatter = StructuredLogFormatter()
        handler.setFormatter(formatter)

        logger = logging.getLogger("test_error_field")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # This should not raise an exception
        logger.error("Test message", extra={"error": "some error details"})

        # Verify the log was written
        output = stream.getvalue()
        assert output.strip() != ""

        # Parse the JSON output
        log_data = json.loads(output.strip())

        # Verify the error field is handled correctly
        assert log_data["message"] == "Test message"
        assert log_data["error_details"] == "some error details"
        # Ensure 'error' is not in the extra section to avoid conflicts
        if "extra" in log_data:
            assert "error" not in log_data["extra"]

    def test_error_field_with_structured_logger(self):
        """Test error field handling with get_logger function."""
        # Create logger with forced JSON output
        logger = get_logger("test_structured_error", force_json=True)

        # This should not raise an exception
        try:
            logger.error(
                "Request failed",
                extra={
                    "error": "Database connection timeout",
                    "user_id": "user123",
                    "request_id": "req789",
                },
            )
        except TypeError as e:
            if "unexpected keyword argument 'error'" in str(e):
                raise AssertionError("The 'error' field fix is not working correctly")
            else:
                raise

    def test_various_error_field_types(self):
        """Test different types of values for the 'error' field."""
        logger = get_logger("test_error_types", force_json=True)

        test_cases = [
            "string error",
            Exception("test exception"),
            {"nested": "error object"},
            ["list", "of", "errors"],
            42,
            None,
        ]

        for error_value in test_cases:
            try:
                logger.info("Test message", extra={"error": error_value})
            except TypeError as e:
                if "unexpected keyword argument 'error'" in str(e):
                    raise AssertionError(
                        f"Error field handling failed for type {type(error_value)}: {error_value}"
                    )
                else:
                    raise

    # @pytest.mark.skipif(not SENTRY_AVAILABLE, reason="Sentry integration not available")
    def test_error_field_with_sentry_integration(self):
        """Test error field handling with Sentry integration enabled."""
        sentry_config = SentryConfig(
            dsn=None, min_level=logging.ERROR  # No DSN so it won't actually initialize
        )

        logger_config = LoggerConfig(enable_sentry=True, sentry_config=sentry_config)

        logger = get_logger("test_sentry_error", config=logger_config, force_json=True)

        # This should not raise an exception
        try:
            logger.error(
                "Sentry test message",
                extra={"error": "some error details", "user_id": "test123"},
            )
        except TypeError as e:
            if "unexpected keyword argument 'error'" in str(e):
                raise AssertionError(
                    "The 'error' field fix is not working with Sentry integration"
                )
            else:
                raise

    def test_error_field_excluded_from_extra_attrs(self):
        """Test that 'error' field is properly excluded from extra attributes processing."""
        config = LoggerConfig()

        # Verify 'error' is in the excluded attributes list
        assert "error" in config.excluded_attrs

        # Create formatter and test
        formatter = StructuredLogFormatter(config)

        # Create a mock log record
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Add error field to the record
        record.error = "test error value"
        record.custom_field = "custom123"  # This should appear in extra

        # Format the record
        formatted = formatter.format(record)
        log_data = json.loads(formatted)

        # Verify error_details is present (explicitly handled)
        assert log_data["error_details"] == "test error value"

        # Verify custom_field is in extra (not excluded)
        assert "extra" in log_data
        assert log_data["extra"]["custom_field"] == "custom123"

        # Verify 'error' is not in extra (excluded)
        assert "error" not in log_data["extra"]

    def test_railway_production_scenario(self):
        """Test the specific Railway production scenario that was failing."""
        import os

        # Simulate Railway environment
        original_env = os.environ.get("RAILWAY_ENVIRONMENT")
        os.environ["RAILWAY_ENVIRONMENT"] = "production"

        try:
            # This simulates the exact scenario that was failing
            logger = get_logger("railway_app")

            # This type of call was causing the TypeError
            logger.error(
                "Request processing failed",
                extra={
                    "error": "Database connection timeout",
                    "user_id": "user123",
                    "company_id": "company456",
                    "request_id": "req789",
                    "status_code": 500,
                },
            )

        except TypeError as e:
            if "unexpected keyword argument 'error'" in str(e):
                raise AssertionError(
                    "Railway production scenario still failing after fix"
                )
            else:
                raise
        finally:
            # Restore environment
            if original_env is not None:
                os.environ["RAILWAY_ENVIRONMENT"] = original_env
            else:
                os.environ.pop("RAILWAY_ENVIRONMENT", None)


if __name__ == "__main__":
    # Run tests directly
    test_instance = TestErrorFieldHandling()

    print("Running error field handling tests...")

    test_methods = [
        test_instance.test_error_field_in_basic_logger,
        test_instance.test_error_field_with_structured_logger,
        test_instance.test_various_error_field_types,
        test_instance.test_error_field_excluded_from_extra_attrs,
        test_instance.test_railway_production_scenario,
    ]

    if SENTRY_AVAILABLE:
        test_methods.append(test_instance.test_error_field_with_sentry_integration)

    for test_method in test_methods:
        try:
            test_method()
            print(f"✓ {test_method.__name__}")
        except Exception as e:
            print(f"✗ {test_method.__name__}: {e}")
            raise

    print("All error field handling tests passed!")
