"""
Tests for gunicorn logger integration functionality.
"""

import json
import logging
from io import StringIO
from unittest.mock import patch

import pytest

from structured_logger import LoggerConfig, setup_gunicorn_logging
from structured_logger.logger import StructuredLogFormatter, _override_gunicorn_loggers


class TestGunicornIntegration:
    """Test gunicorn logger override functionality."""

    def setup_method(self):
        """Setup for each test method."""
        # Clear any existing gunicorn loggers
        for logger_name in [
            "gunicorn",
            "gunicorn.access",
            "gunicorn.error",
        ]:
            logger = logging.getLogger(logger_name)
            logger.handlers.clear()
            logger.setLevel(logging.NOTSET)

    def test_gunicorn_logger_override_disabled_by_default(self):
        """Test that gunicorn logger override is disabled by default."""
        config = LoggerConfig()
        assert config.override_gunicorn_loggers is False

    def test_gunicorn_logger_override_configuration(self):
        """Test gunicorn logger override configuration."""
        config = LoggerConfig(override_gunicorn_loggers=True)
        assert config.override_gunicorn_loggers is True
        assert "gunicorn" in config.gunicorn_loggers
        assert "gunicorn.access" in config.gunicorn_loggers
        assert "gunicorn.error" in config.gunicorn_loggers

    def test_override_gunicorn_loggers_function(self):
        """Test the _override_gunicorn_loggers function."""
        config = LoggerConfig(override_gunicorn_loggers=True)
        formatter = StructuredLogFormatter(config)

        # Mock the production environment check to return False (dev mode)
        with patch(
            "structured_logger.logger._is_production_environment", return_value=False
        ):
            _override_gunicorn_loggers(config, formatter, force_json=True)

        # Check that gunicorn loggers have been configured
        for logger_name in config.gunicorn_loggers:
            logger = logging.getLogger(logger_name)
            assert len(logger.handlers) > 0
            assert logger.propagate is False

    def test_override_gunicorn_loggers_with_structured_formatting(self):
        """Test that gunicorn loggers use structured formatting when overridden."""
        config = LoggerConfig(override_gunicorn_loggers=True)
        formatter = StructuredLogFormatter(config)

        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)

        with patch(
            "structured_logger.logger._is_production_environment", return_value=True
        ):
            _override_gunicorn_loggers(config, formatter, force_json=True)

        # Get gunicorn logger and test it
        gunicorn_logger = logging.getLogger("gunicorn")
        gunicorn_logger.handlers.clear()  # Clear the handler added by override
        gunicorn_logger.addHandler(handler)

        # Set formatter manually for testing
        handler.setFormatter(StructuredLogFormatter(config))

        # Log a message
        gunicorn_logger.info("Test gunicorn message")

        # Get the logged output
        log_output = log_capture.getvalue().strip()

        # Verify it's valid JSON
        try:
            log_data = json.loads(log_output)
            assert log_data["level"] == "INFO"
            assert log_data["message"] == "Test gunicorn message"
            assert log_data["module"] == "gunicorn"
            assert "time" in log_data
        except json.JSONDecodeError:
            pytest.fail("Log output is not valid JSON")

    def test_setup_gunicorn_logging_function(self):
        """Test the setup_gunicorn_logging convenience function."""
        # Call the setup function
        with patch(
            "structured_logger.logger._is_production_environment", return_value=True
        ):
            setup_gunicorn_logging(force_json=True)

        # Verify gunicorn loggers are configured
        for logger_name in ["gunicorn", "gunicorn.access", "gunicorn.error"]:
            logger = logging.getLogger(logger_name)
            assert len(logger.handlers) > 0
            assert logger.propagate is False

    def test_setup_gunicorn_logging_with_custom_config(self):
        """Test setup_gunicorn_logging with custom configuration."""
        config = LoggerConfig(
            custom_fields=["request_id", "user_id"],
            default_log_level="DEBUG",
        )

        with patch(
            "structured_logger.logger._is_production_environment", return_value=True
        ):
            setup_gunicorn_logging(config=config, force_json=True)

        # Verify configuration is applied
        gunicorn_logger = logging.getLogger("gunicorn")
        assert len(gunicorn_logger.handlers) > 0
        assert gunicorn_logger.level == logging.DEBUG

    def test_gunicorn_access_logger_formatting(self):
        """Test that gunicorn.access logger is properly formatted."""
        config = LoggerConfig(override_gunicorn_loggers=True)

        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)

        with patch(
            "structured_logger.logger._is_production_environment", return_value=True
        ):
            setup_gunicorn_logging(config=config, force_json=True)

        # Get gunicorn.access logger
        access_logger = logging.getLogger("gunicorn.access")
        access_logger.handlers.clear()
        access_logger.addHandler(handler)
        handler.setFormatter(StructuredLogFormatter(config))

        # Log an access message
        access_logger.info('127.0.0.1 - - "GET /api/users HTTP/1.1" 200 1234')

        # Get the logged output
        log_output = log_capture.getvalue().strip()

        # Verify it's valid JSON
        try:
            log_data = json.loads(log_output)
            assert log_data["level"] == "INFO"
            assert "GET /api/users" in log_data["message"]
            assert log_data["module"] == "gunicorn.access"
        except json.JSONDecodeError:
            pytest.fail("Access log output is not valid JSON")

    def test_gunicorn_error_logger_formatting(self):
        """Test that gunicorn.error logger is properly formatted."""
        config = LoggerConfig(override_gunicorn_loggers=True)

        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)

        with patch(
            "structured_logger.logger._is_production_environment", return_value=True
        ):
            setup_gunicorn_logging(config=config, force_json=True)

        # Get gunicorn.error logger
        error_logger = logging.getLogger("gunicorn.error")
        error_logger.handlers.clear()
        error_logger.addHandler(handler)
        handler.setFormatter(StructuredLogFormatter(config))

        # Log an error message
        error_logger.error("Worker failed to boot")

        # Get the logged output
        log_output = log_capture.getvalue().strip()

        # Verify it's valid JSON
        try:
            log_data = json.loads(log_output)
            assert log_data["level"] == "ERROR"
            assert log_data["message"] == "Worker failed to boot"
            assert log_data["module"] == "gunicorn.error"
        except json.JSONDecodeError:
            pytest.fail("Error log output is not valid JSON")

    def test_custom_gunicorn_loggers_list(self):
        """Test configuring custom list of gunicorn loggers to override."""
        config = LoggerConfig(
            override_gunicorn_loggers=True,
            gunicorn_loggers=["gunicorn", "gunicorn.access"],  # Only these two
        )
        formatter = StructuredLogFormatter(config)

        with patch(
            "structured_logger.logger._is_production_environment", return_value=True
        ):
            _override_gunicorn_loggers(config, formatter, force_json=True)

        # Check configured loggers
        assert len(logging.getLogger("gunicorn").handlers) > 0
        assert len(logging.getLogger("gunicorn.access").handlers) > 0

    def test_gunicorn_logger_no_propagation(self):
        """Test that gunicorn loggers don't propagate to root logger."""
        config = LoggerConfig(override_gunicorn_loggers=True)
        formatter = StructuredLogFormatter(config)

        with patch(
            "structured_logger.logger._is_production_environment", return_value=True
        ):
            _override_gunicorn_loggers(config, formatter, force_json=True)

        # Verify propagate is False for all gunicorn loggers
        for logger_name in config.gunicorn_loggers:
            logger = logging.getLogger(logger_name)
            assert logger.propagate is False

    def test_gunicorn_logger_with_extra_fields(self):
        """Test gunicorn logger with custom extra fields."""
        config = LoggerConfig(
            override_gunicorn_loggers=True,
            custom_fields=["request_id", "user_id"],
        )

        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)

        with patch(
            "structured_logger.logger._is_production_environment", return_value=True
        ):
            setup_gunicorn_logging(config=config, force_json=True)

        # Get gunicorn logger
        gunicorn_logger = logging.getLogger("gunicorn")
        gunicorn_logger.handlers.clear()
        gunicorn_logger.addHandler(handler)
        handler.setFormatter(StructuredLogFormatter(config))

        # Log with extra fields
        gunicorn_logger.info(
            "Request processed",
            extra={"request_id": "req-123", "user_id": "user-456"},
        )

        # Get the logged output
        log_output = log_capture.getvalue().strip()

        # Verify extra fields are included
        try:
            log_data = json.loads(log_output)
            assert log_data["request_id"] == "req-123"
            assert log_data["user_id"] == "user-456"
        except json.JSONDecodeError:
            pytest.fail("Log output is not valid JSON")

    def test_gunicorn_logger_force_dev_format(self):
        """Test gunicorn logger with forced development format."""
        config = LoggerConfig(override_gunicorn_loggers=True)

        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)

        with patch(
            "structured_logger.logger._is_production_environment", return_value=True
        ):
            setup_gunicorn_logging(config=config, force_dev=True)

        # Get gunicorn logger
        gunicorn_logger = logging.getLogger("gunicorn")
        gunicorn_logger.handlers.clear()
        gunicorn_logger.addHandler(handler)

        # Use dev formatter
        dev_formatter = logging.Formatter(config.dev_format)
        handler.setFormatter(dev_formatter)

        # Log a message
        gunicorn_logger.info("Test message")

        # Get the logged output
        log_output = log_capture.getvalue().strip()

        # Verify it's NOT JSON (should be dev format)
        assert "[INFO]" in log_output
        assert "gunicorn" in log_output
        assert "Test message" in log_output

    def test_gunicorn_logger_environment_detection(self):
        """Test that gunicorn logger respects environment detection."""
        config = LoggerConfig(override_gunicorn_loggers=True)
        formatter = StructuredLogFormatter(config)

        # Test production environment
        with patch(
            "structured_logger.logger._is_production_environment", return_value=True
        ):
            _override_gunicorn_loggers(config, formatter)

        gunicorn_logger = logging.getLogger("gunicorn")
        assert len(gunicorn_logger.handlers) > 0

        # Clear handlers
        gunicorn_logger.handlers.clear()

        # Test development environment
        with patch(
            "structured_logger.logger._is_production_environment", return_value=False
        ):
            _override_gunicorn_loggers(config, formatter)

        assert len(gunicorn_logger.handlers) > 0

    @patch.dict("os.environ", {"LOG_LEVEL": "WARNING"})
    def test_gunicorn_logger_respects_log_level_env_var(self):
        """Test that gunicorn logger respects LOG_LEVEL environment variable."""
        config = LoggerConfig(override_gunicorn_loggers=True)
        formatter = StructuredLogFormatter(config)

        with patch(
            "structured_logger.logger._is_production_environment", return_value=True
        ):
            _override_gunicorn_loggers(config, formatter, force_json=True)

        gunicorn_logger = logging.getLogger("gunicorn")
        assert gunicorn_logger.level == logging.WARNING

    def test_gunicorn_logger_override_when_disabled(self):
        """Test that override does nothing when disabled."""
        config = LoggerConfig(override_gunicorn_loggers=False)
        formatter = StructuredLogFormatter(config)

        # Clear any existing handlers
        for logger_name in config.gunicorn_loggers:
            logger = logging.getLogger(logger_name)
            logger.handlers.clear()

        # Call override function
        _override_gunicorn_loggers(config, formatter, force_json=True)

        # Verify no handlers were added
        for logger_name in config.gunicorn_loggers:
            logger = logging.getLogger(logger_name)
            assert len(logger.handlers) == 0
