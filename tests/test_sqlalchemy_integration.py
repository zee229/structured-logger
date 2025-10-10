"""
Tests for SQLAlchemy logger integration functionality.
"""

import json
import logging
from io import StringIO
from unittest.mock import patch

import pytest

from structured_logger import LoggerConfig, get_logger
from structured_logger.logger import (
    StructuredLogFormatter,
    _override_sqlalchemy_loggers,
)


class TestSQLAlchemyLoggerIntegration:
    """Test SQLAlchemy logger override functionality."""

    def setup_method(self):
        """Setup for each test method."""
        # Clear any existing SQLAlchemy loggers
        sqlalchemy_loggers = [
            "sqlalchemy",
            "sqlalchemy.engine",
            "sqlalchemy.pool",
            "sqlalchemy.orm",
        ]
        for logger_name in sqlalchemy_loggers:
            logger = logging.getLogger(logger_name)
            logger.handlers.clear()
            logger.setLevel(logging.NOTSET)
            logger.propagate = True

    def test_sqlalchemy_logging_disabled_by_default(self):
        """Test that SQLAlchemy logging is disabled by default."""
        config = LoggerConfig()
        assert config.enable_sqlalchemy_logging is False

    def test_sqlalchemy_logging_can_be_enabled(self):
        """Test that SQLAlchemy logging can be enabled."""
        config = LoggerConfig(enable_sqlalchemy_logging=True)
        assert config.enable_sqlalchemy_logging is True

    def test_sqlalchemy_loggers_configuration(self):
        """Test SQLAlchemy logger configuration."""
        config = LoggerConfig()
        assert "sqlalchemy" in config.sqlalchemy_loggers
        assert "sqlalchemy.engine" in config.sqlalchemy_loggers
        assert "sqlalchemy.pool" in config.sqlalchemy_loggers
        assert "sqlalchemy.orm" in config.sqlalchemy_loggers

    def test_sqlalchemy_log_level_default(self):
        """Test that SQLAlchemy log level defaults to WARNING."""
        config = LoggerConfig()
        assert config.sqlalchemy_log_level == "WARNING"

    def test_sqlalchemy_loggers_silenced_when_disabled(self):
        """Test that SQLAlchemy loggers are silenced when disabled."""
        config = LoggerConfig(enable_sqlalchemy_logging=False)
        formatter = StructuredLogFormatter(config)

        with patch(
            "structured_logger.logger._is_production_environment", return_value=False
        ):
            _override_sqlalchemy_loggers(config, formatter, force_json=True)

        # Check that SQLAlchemy loggers are silenced
        for logger_name in config.sqlalchemy_loggers:
            logger = logging.getLogger(logger_name)
            # Should be set to CRITICAL+1 which is effectively silent
            assert logger.level > logging.CRITICAL
            assert logger.propagate is False

    def test_sqlalchemy_loggers_enabled_when_configured(self):
        """Test that SQLAlchemy loggers are enabled when configured."""
        config = LoggerConfig(enable_sqlalchemy_logging=True)
        formatter = StructuredLogFormatter(config)

        with patch(
            "structured_logger.logger._is_production_environment", return_value=False
        ):
            _override_sqlalchemy_loggers(config, formatter, force_json=True)

        # Check that SQLAlchemy loggers have been configured
        for logger_name in config.sqlalchemy_loggers:
            logger = logging.getLogger(logger_name)
            assert len(logger.handlers) > 0
            assert logger.level == logging.WARNING
            assert logger.propagate is False

    def test_sqlalchemy_logger_structured_formatting(self):
        """Test that SQLAlchemy logger uses structured formatting when enabled."""
        config = LoggerConfig(enable_sqlalchemy_logging=True)
        formatter = StructuredLogFormatter(config)

        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)

        with patch(
            "structured_logger.logger._is_production_environment", return_value=True
        ):
            _override_sqlalchemy_loggers(config, formatter, force_json=True)

        # Get sqlalchemy logger and test it
        sqlalchemy_logger = logging.getLogger("sqlalchemy")
        sqlalchemy_logger.handlers.clear()
        sqlalchemy_logger.addHandler(handler)
        handler.setFormatter(StructuredLogFormatter(config))

        # Log a message
        sqlalchemy_logger.warning("Database connection warning")

        # Get the logged output
        log_output = log_capture.getvalue().strip()

        # Verify it's valid JSON
        try:
            log_data = json.loads(log_output)
            assert log_data["level"] == "WARNING"
            assert log_data["message"] == "Database connection warning"
            assert log_data["module"] == "sqlalchemy"
        except json.JSONDecodeError:
            pytest.fail("Log output is not valid JSON")

    def test_sqlalchemy_custom_log_level(self):
        """Test that SQLAlchemy log level can be customized."""
        config = LoggerConfig(
            enable_sqlalchemy_logging=True, sqlalchemy_log_level="ERROR"
        )
        formatter = StructuredLogFormatter(config)

        with patch(
            "structured_logger.logger._is_production_environment", return_value=False
        ):
            _override_sqlalchemy_loggers(config, formatter, force_json=True)

        # Check that SQLAlchemy logger has ERROR level
        sqlalchemy_logger = logging.getLogger("sqlalchemy")
        assert sqlalchemy_logger.level == logging.ERROR

    def test_sqlalchemy_logger_with_get_logger(self):
        """Test SQLAlchemy logging control via get_logger."""
        # Test with disabled (default)
        config = LoggerConfig(enable_sqlalchemy_logging=False)
        logger = get_logger("test_logger_disabled", config=config)

        sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
        assert sqlalchemy_logger.level > logging.CRITICAL

        # Clear handlers completely for a clean test
        for logger_name in ["test_logger_disabled", "test_logger_enabled"] + list(
            config.sqlalchemy_loggers
        ):
            test_logger = logging.getLogger(logger_name)
            test_logger.handlers.clear()
            test_logger.setLevel(logging.NOTSET)
            test_logger.propagate = True

        # Test with enabled using a different logger name
        config = LoggerConfig(enable_sqlalchemy_logging=True)
        logger = get_logger("test_logger_enabled", config=config)

        sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
        assert sqlalchemy_logger.level == logging.WARNING
        assert len(sqlalchemy_logger.handlers) > 0

    def test_sqlalchemy_engine_logger(self):
        """Test that sqlalchemy.engine logger works correctly."""
        config = LoggerConfig(
            enable_sqlalchemy_logging=True, sqlalchemy_log_level="INFO"
        )
        formatter = StructuredLogFormatter(config)

        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(StructuredLogFormatter(config))

        with patch(
            "structured_logger.logger._is_production_environment", return_value=True
        ):
            _override_sqlalchemy_loggers(config, formatter, force_json=True)

        # Get sqlalchemy.engine logger
        engine_logger = logging.getLogger("sqlalchemy.engine")
        engine_logger.handlers.clear()
        engine_logger.addHandler(handler)

        # Log a message
        engine_logger.info("SELECT * FROM users")

        log_output = log_capture.getvalue().strip()

        # Verify it's valid JSON
        try:
            log_data = json.loads(log_output)
            assert log_data["level"] == "INFO"
            assert "SELECT" in log_data["message"]
            assert log_data["module"] == "sqlalchemy.engine"
        except json.JSONDecodeError:
            pytest.fail("Log output is not valid JSON")

    def test_sqlalchemy_logger_prevents_duplicate_logs(self):
        """Test that SQLAlchemy loggers don't propagate to prevent duplicates."""
        config = LoggerConfig(enable_sqlalchemy_logging=True)
        formatter = StructuredLogFormatter(config)

        with patch(
            "structured_logger.logger._is_production_environment", return_value=True
        ):
            _override_sqlalchemy_loggers(config, formatter, force_json=True)

        # Check that all SQLAlchemy loggers have propagate=False
        for logger_name in config.sqlalchemy_loggers:
            logger = logging.getLogger(logger_name)
            assert logger.propagate is False, f"{logger_name} should not propagate"

    def test_sqlalchemy_logger_respects_force_dev(self):
        """Test that SQLAlchemy logger override respects force_dev parameter."""
        config = LoggerConfig(enable_sqlalchemy_logging=True)
        formatter = StructuredLogFormatter(config)

        with patch(
            "structured_logger.logger._is_production_environment", return_value=True
        ):
            _override_sqlalchemy_loggers(config, formatter, force_dev=True)

        # Get sqlalchemy logger and check its handler
        sqlalchemy_logger = logging.getLogger("sqlalchemy")

        # The logger should have handlers with regular formatter when force_dev=True
        assert len(sqlalchemy_logger.handlers) > 0
        # Check that the formatter is not a StructuredLogFormatter when force_dev=True
        handler_formatter = sqlalchemy_logger.handlers[0].formatter
        assert not isinstance(handler_formatter, StructuredLogFormatter)

    def test_custom_sqlalchemy_loggers_list(self):
        """Test that custom SQLAlchemy logger list is respected."""
        custom_loggers = ["sqlalchemy.engine"]
        config = LoggerConfig(
            enable_sqlalchemy_logging=True,
            sqlalchemy_loggers=custom_loggers,
        )
        formatter = StructuredLogFormatter(config)

        with patch(
            "structured_logger.logger._is_production_environment", return_value=False
        ):
            _override_sqlalchemy_loggers(config, formatter, force_json=True)

        # Check that only custom loggers have been configured
        engine_logger = logging.getLogger("sqlalchemy.engine")
        assert len(engine_logger.handlers) > 0
        assert engine_logger.propagate is False

        # Check that other sqlalchemy loggers are not configured
        pool_logger = logging.getLogger("sqlalchemy.pool")
        assert len(pool_logger.handlers) == 0

    def test_sqlalchemy_logger_with_extra_fields(self):
        """Test that SQLAlchemy loggers support extra fields."""
        config = LoggerConfig(
            enable_sqlalchemy_logging=True,
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
            _override_sqlalchemy_loggers(config, formatter, force_json=True)

        # Get sqlalchemy logger
        sqlalchemy_logger = logging.getLogger("sqlalchemy")
        sqlalchemy_logger.handlers.clear()
        sqlalchemy_logger.addHandler(handler)

        # Log with extra fields
        sqlalchemy_logger.warning(
            "Slow query",
            extra={"request_id": "123", "user_id": "456", "duration_ms": 1500},
        )

        log_output = log_capture.getvalue().strip()

        # Verify extra fields are included
        try:
            log_data = json.loads(log_output)
            assert log_data["request_id"] == "123"
            assert log_data["user_id"] == "456"
            # duration_ms should be in extra since it's not a custom field
            assert "extra" in log_data
            assert log_data["extra"]["duration_ms"] == 1500
        except json.JSONDecodeError:
            pytest.fail("Log output is not valid JSON")

    def test_sqlalchemy_info_logs_silenced_by_default(self):
        """Test that INFO level SQLAlchemy logs are silenced by default WARNING level."""
        config = LoggerConfig(enable_sqlalchemy_logging=True)
        formatter = StructuredLogFormatter(config)

        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(StructuredLogFormatter(config))

        with patch(
            "structured_logger.logger._is_production_environment", return_value=True
        ):
            _override_sqlalchemy_loggers(config, formatter, force_json=True)

        # Get sqlalchemy logger
        sqlalchemy_logger = logging.getLogger("sqlalchemy")
        sqlalchemy_logger.handlers.clear()
        sqlalchemy_logger.addHandler(handler)

        # Try to log INFO message (should be filtered out)
        sqlalchemy_logger.info("This should not appear")

        # Try to log WARNING message (should appear)
        sqlalchemy_logger.warning("This should appear")

        log_output = log_capture.getvalue().strip()

        # Should only contain the WARNING message
        assert "This should not appear" not in log_output
        assert "This should appear" in log_output
