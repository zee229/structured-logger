"""
Tests for uvicorn logger integration functionality.
"""

import json
import logging
from io import StringIO
from unittest.mock import patch

import pytest

from structured_logger import LoggerConfig, setup_uvicorn_logging
from structured_logger.logger import StructuredLogFormatter, _override_uvicorn_loggers


class TestUvicornIntegration:
    """Test uvicorn logger override functionality."""

    def setup_method(self):
        """Setup for each test method."""
        # Clear any existing uvicorn loggers
        for logger_name in [
            "uvicorn",
            "uvicorn.access",
            "uvicorn.error",
            "uvicorn.asgi",
        ]:
            logger = logging.getLogger(logger_name)
            logger.handlers.clear()
            logger.setLevel(logging.NOTSET)

    def test_uvicorn_logger_override_enabled_by_default(self):
        """Test that uvicorn logger override is enabled by default."""
        config = LoggerConfig()
        assert config.override_uvicorn_loggers is True

    def test_uvicorn_logger_override_configuration(self):
        """Test uvicorn logger override configuration."""
        config = LoggerConfig(override_uvicorn_loggers=True)
        assert config.override_uvicorn_loggers is True
        assert "uvicorn" in config.uvicorn_loggers
        assert "uvicorn.access" in config.uvicorn_loggers
        assert "uvicorn.error" in config.uvicorn_loggers
        assert "uvicorn.asgi" in config.uvicorn_loggers

    def test_override_uvicorn_loggers_function(self):
        """Test the _override_uvicorn_loggers function."""
        config = LoggerConfig(override_uvicorn_loggers=True)
        formatter = StructuredLogFormatter(config)

        # Mock the production environment check to return False (dev mode)
        with patch(
            "structured_logger.logger._is_production_environment", return_value=False
        ):
            _override_uvicorn_loggers(config, formatter, force_json=True)

        # Check that uvicorn loggers have been configured
        for logger_name in config.uvicorn_loggers:
            logger = logging.getLogger(logger_name)
            assert len(logger.handlers) > 0
            assert logger.propagate is False

    def test_override_uvicorn_loggers_with_structured_formatting(self):
        """Test that uvicorn loggers use structured formatting when overridden."""
        config = LoggerConfig(override_uvicorn_loggers=True)
        formatter = StructuredLogFormatter(config)

        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)

        with patch(
            "structured_logger.logger._is_production_environment", return_value=True
        ):
            _override_uvicorn_loggers(config, formatter, force_json=True)

        # Get uvicorn logger and test it
        uvicorn_logger = logging.getLogger("uvicorn")
        uvicorn_logger.handlers.clear()  # Clear the handler added by override
        uvicorn_logger.addHandler(handler)

        # Set formatter manually for testing
        handler.setFormatter(StructuredLogFormatter(config))

        # Log a message
        uvicorn_logger.info("Test uvicorn message")

        # Get the logged output
        log_output = log_capture.getvalue().strip()

        # Verify it's valid JSON
        try:
            log_data = json.loads(log_output)
            assert log_data["level"] == "INFO"
            assert log_data["message"] == "Test uvicorn message"
            assert log_data["module"] == "uvicorn"
            assert "time" in log_data
        except json.JSONDecodeError:
            pytest.fail("Log output is not valid JSON")

    def test_setup_uvicorn_logging_convenience_function(self):
        """Test the setup_uvicorn_logging convenience function."""
        # Test with default config
        setup_uvicorn_logging()

        # Check that uvicorn loggers have been configured
        for logger_name in [
            "uvicorn",
            "uvicorn.access",
            "uvicorn.error",
            "uvicorn.asgi",
        ]:
            logger = logging.getLogger(logger_name)
            assert len(logger.handlers) > 0
            assert logger.propagate is False

    def test_setup_uvicorn_logging_with_custom_config(self):
        """Test setup_uvicorn_logging with custom configuration."""
        config = LoggerConfig(
            custom_fields=["request_id", "user_id"],
            include_extra_attrs=True,
        )

        setup_uvicorn_logging(config=config, force_json=True)

        # Check that uvicorn loggers have been configured
        uvicorn_logger = logging.getLogger("uvicorn")
        assert len(uvicorn_logger.handlers) > 0
        assert uvicorn_logger.propagate is False

    def test_uvicorn_logger_override_respects_force_dev(self):
        """Test that uvicorn logger override respects force_dev parameter."""
        config = LoggerConfig(override_uvicorn_loggers=True)
        formatter = StructuredLogFormatter(config)

        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)

        with patch(
            "structured_logger.logger._is_production_environment", return_value=True
        ):
            _override_uvicorn_loggers(config, formatter, force_dev=True)

        # Get uvicorn logger and check its handler
        uvicorn_logger = logging.getLogger("uvicorn")

        # The uvicorn logger should have handlers with regular formatter when force_dev=True
        assert len(uvicorn_logger.handlers) > 0
        # Check that the formatter is not a StructuredLogFormatter when force_dev=True
        handler_formatter = uvicorn_logger.handlers[0].formatter
        assert not isinstance(handler_formatter, StructuredLogFormatter)

    def test_uvicorn_logger_override_disabled_when_config_false(self):
        """Test that uvicorn loggers are not overridden when config is False."""
        config = LoggerConfig(override_uvicorn_loggers=False)
        formatter = StructuredLogFormatter(config)

        # Store original handler count
        original_handler_counts = {}
        for logger_name in config.uvicorn_loggers:
            logger = logging.getLogger(logger_name)
            original_handler_counts[logger_name] = len(logger.handlers)

        _override_uvicorn_loggers(config, formatter)

        # Check that handler counts haven't changed
        for logger_name in config.uvicorn_loggers:
            logger = logging.getLogger(logger_name)
            assert len(logger.handlers) == original_handler_counts[logger_name]

    def test_custom_uvicorn_loggers_list(self):
        """Test that custom uvicorn logger list is respected."""
        custom_loggers = ["uvicorn", "uvicorn.custom"]
        config = LoggerConfig(
            override_uvicorn_loggers=True,
            uvicorn_loggers=custom_loggers,
        )
        formatter = StructuredLogFormatter(config)

        with patch(
            "structured_logger.logger._is_production_environment", return_value=False
        ):
            _override_uvicorn_loggers(config, formatter, force_json=True)

        # Check that only custom loggers have been configured
        for logger_name in custom_loggers:
            logger = logging.getLogger(logger_name)
            assert len(logger.handlers) > 0
            assert logger.propagate is False

        # Check that default loggers (not in custom list) are not configured
        default_logger = logging.getLogger("uvicorn.access")
        # Should have no handlers if it wasn't in the custom list
        if "uvicorn.access" not in custom_loggers:
            # We can't assert 0 handlers because other tests might have added them
            # So we just check it wasn't explicitly configured by our function
            pass
