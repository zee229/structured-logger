"""
Tests for third-party library logger integration functionality.
"""

import json
import logging
from io import StringIO
from unittest.mock import patch

import pytest

from structured_logger import LoggerConfig, setup_library_logging
from structured_logger.logger import StructuredLogFormatter, _override_library_loggers


class TestLibraryLoggerIntegration:
    """Test third-party library logger override functionality."""

    def setup_method(self):
        """Setup for each test method."""
        # Clear any existing library loggers
        library_loggers = [
            "httpx",
            "httpcore",
            "starlette",
            "fastapi",
            "asyncio",
            "aiohttp",
            "urllib3",
            "requests",
        ]
        for logger_name in library_loggers:
            logger = logging.getLogger(logger_name)
            logger.handlers.clear()
            logger.setLevel(logging.NOTSET)

    def test_library_logger_override_enabled_by_default(self):
        """Test that library logger override is enabled by default."""
        config = LoggerConfig()
        assert config.override_library_loggers is True

    def test_library_logger_override_configuration(self):
        """Test library logger override configuration."""
        config = LoggerConfig(override_library_loggers=True)
        assert config.override_library_loggers is True
        assert "httpx" in config.library_loggers
        assert "starlette" in config.library_loggers
        assert "fastapi" in config.library_loggers
        # SQLAlchemy is now in a separate list
        assert "sqlalchemy" not in config.library_loggers
        assert "sqlalchemy" in config.sqlalchemy_loggers

    def test_library_logger_override_can_be_disabled(self):
        """Test that library logger override can be disabled."""
        config = LoggerConfig(override_library_loggers=False)
        assert config.override_library_loggers is False

    def test_override_library_loggers_function(self):
        """Test the _override_library_loggers function."""
        config = LoggerConfig(override_library_loggers=True)
        formatter = StructuredLogFormatter(config)

        # Mock the production environment check to return False (dev mode)
        with patch(
            "structured_logger.logger._is_production_environment", return_value=False
        ):
            _override_library_loggers(config, formatter, force_json=True)

        # Check that library loggers have been configured
        for logger_name in ["httpx", "starlette"]:
            logger = logging.getLogger(logger_name)
            assert len(logger.handlers) > 0
            assert logger.propagate is False

    def test_override_library_loggers_with_structured_formatting(self):
        """Test that library loggers use structured formatting when overridden."""
        config = LoggerConfig(override_library_loggers=True)
        formatter = StructuredLogFormatter(config)

        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)

        with patch(
            "structured_logger.logger._is_production_environment", return_value=True
        ):
            _override_library_loggers(config, formatter, force_json=True)

        # Get httpx logger and test it
        httpx_logger = logging.getLogger("httpx")
        httpx_logger.handlers.clear()  # Clear the handler added by override
        httpx_logger.addHandler(handler)

        # Set formatter manually for testing
        handler.setFormatter(StructuredLogFormatter(config))

        # Log a message
        httpx_logger.info("Test httpx message")

        # Get the logged output
        log_output = log_capture.getvalue().strip()

        # Verify it's valid JSON
        try:
            log_data = json.loads(log_output)
            assert log_data["level"] == "INFO"
            assert log_data["message"] == "Test httpx message"
            assert log_data["module"] == "httpx"
            assert "time" in log_data
        except json.JSONDecodeError:
            pytest.fail("Log output is not valid JSON")

    def test_setup_library_logging_convenience_function(self):
        """Test the setup_library_logging convenience function."""
        # Test with default config
        setup_library_logging()

        # Check that library loggers have been configured
        for logger_name in ["httpx", "starlette", "fastapi"]:
            logger = logging.getLogger(logger_name)
            assert len(logger.handlers) > 0
            assert logger.propagate is False

    def test_setup_library_logging_with_custom_config(self):
        """Test setup_library_logging with custom configuration."""
        config = LoggerConfig(
            custom_fields=["request_id", "user_id"],
            include_extra_attrs=True,
        )

        setup_library_logging(config=config, force_json=True)

        # Check that library loggers have been configured
        httpx_logger = logging.getLogger("httpx")
        assert len(httpx_logger.handlers) > 0
        assert httpx_logger.propagate is False

    def test_library_logger_override_respects_force_dev(self):
        """Test that library logger override respects force_dev parameter."""
        config = LoggerConfig(override_library_loggers=True)
        formatter = StructuredLogFormatter(config)

        with patch(
            "structured_logger.logger._is_production_environment", return_value=True
        ):
            _override_library_loggers(config, formatter, force_dev=True)

        # Get httpx logger and check its handler
        httpx_logger = logging.getLogger("httpx")

        # The library logger should have handlers with regular formatter when force_dev=True
        assert len(httpx_logger.handlers) > 0
        # Check that the formatter is not a StructuredLogFormatter when force_dev=True
        handler_formatter = httpx_logger.handlers[0].formatter
        assert not isinstance(handler_formatter, StructuredLogFormatter)

    def test_library_logger_override_disabled_when_config_false(self):
        """Test that library loggers are not overridden when config is False."""
        config = LoggerConfig(override_library_loggers=False)
        formatter = StructuredLogFormatter(config)

        # Store original handler count
        original_handler_counts = {}
        for logger_name in ["httpx", "starlette"]:
            logger = logging.getLogger(logger_name)
            original_handler_counts[logger_name] = len(logger.handlers)

        _override_library_loggers(config, formatter)

        # Check that handler counts haven't changed
        for logger_name in ["httpx", "starlette"]:
            logger = logging.getLogger(logger_name)
            assert len(logger.handlers) == original_handler_counts[logger_name]

    def test_custom_library_loggers_list(self):
        """Test that custom library logger list is respected."""
        custom_loggers = ["httpx", "mylib"]
        config = LoggerConfig(
            override_library_loggers=True,
            library_loggers=custom_loggers,
        )
        formatter = StructuredLogFormatter(config)

        with patch(
            "structured_logger.logger._is_production_environment", return_value=False
        ):
            _override_library_loggers(config, formatter, force_json=True)

        # Check that only custom loggers have been configured
        for logger_name in custom_loggers:
            logger = logging.getLogger(logger_name)
            assert len(logger.handlers) > 0
            assert logger.propagate is False

    def test_multiple_library_loggers_formatted_consistently(self):
        """Test that multiple library loggers are formatted consistently."""
        config = LoggerConfig(override_library_loggers=True)
        formatter = StructuredLogFormatter(config)

        with patch(
            "structured_logger.logger._is_production_environment", return_value=True
        ):
            _override_library_loggers(config, formatter, force_json=True)

        # Test multiple loggers
        test_loggers = ["httpx", "starlette"]

        for logger_name in test_loggers:
            log_capture = StringIO()
            handler = logging.StreamHandler(log_capture)
            handler.setFormatter(StructuredLogFormatter(config))

            logger = logging.getLogger(logger_name)
            logger.handlers.clear()
            logger.addHandler(handler)

            logger.info(f"Test message from {logger_name}")

            log_output = log_capture.getvalue().strip()

            # Verify it's valid JSON
            try:
                log_data = json.loads(log_output)
                assert log_data["level"] == "INFO"
                assert log_data["module"] == logger_name
                assert "time" in log_data
            except json.JSONDecodeError:
                pytest.fail(f"Log output from {logger_name} is not valid JSON")

    def test_library_logger_with_extra_fields(self):
        """Test that library loggers support extra fields."""
        config = LoggerConfig(
            override_library_loggers=True,
            custom_fields=["request_id", "user_id"],
        )
        formatter = StructuredLogFormatter(config)

        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(StructuredLogFormatter(config))

        with patch(
            "structured_logger.logger._is_production_environment", return_value=True
        ):
            _override_library_loggers(config, formatter, force_json=True)

        # Get httpx logger
        httpx_logger = logging.getLogger("httpx")
        httpx_logger.handlers.clear()
        httpx_logger.addHandler(handler)

        # Log with extra fields
        httpx_logger.info(
            "HTTP request",
            extra={"request_id": "123", "user_id": "456", "method": "GET"},
        )

        log_output = log_capture.getvalue().strip()

        # Verify extra fields are included
        try:
            log_data = json.loads(log_output)
            assert log_data["request_id"] == "123"
            assert log_data["user_id"] == "456"
            # method should be in extra since it's not a custom field
            assert "extra" in log_data
            assert log_data["extra"]["method"] == "GET"
        except json.JSONDecodeError:
            pytest.fail("Log output is not valid JSON")

    def test_library_logger_override_with_log_level(self):
        """Test that library logger override respects log level configuration."""
        import os

        # Set LOG_LEVEL environment variable
        os.environ["LOG_LEVEL"] = "WARNING"

        try:
            config = LoggerConfig(
                override_library_loggers=True,
                default_log_level="WARNING",
            )
            formatter = StructuredLogFormatter(config)

            with patch(
                "structured_logger.logger._is_production_environment", return_value=True
            ):
                _override_library_loggers(config, formatter, force_json=True)

            # Check that httpx logger has WARNING level
            httpx_logger = logging.getLogger("httpx")
            assert httpx_logger.level == logging.WARNING
        finally:
            # Clean up environment variable
            if "LOG_LEVEL" in os.environ:
                del os.environ["LOG_LEVEL"]

    def test_library_logger_prevents_duplicate_logs(self):
        """Test that library loggers don't propagate to prevent duplicates."""
        config = LoggerConfig(override_library_loggers=True)
        formatter = StructuredLogFormatter(config)

        with patch(
            "structured_logger.logger._is_production_environment", return_value=True
        ):
            _override_library_loggers(config, formatter, force_json=True)

        # Check that all library loggers have propagate=False
        for logger_name in config.library_loggers:
            logger = logging.getLogger(logger_name)
            assert logger.propagate is False, f"{logger_name} should not propagate"
