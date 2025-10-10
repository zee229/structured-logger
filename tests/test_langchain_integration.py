"""
Tests for LangChain logger integration functionality.
"""

import json
import logging
from io import StringIO
from unittest.mock import patch

import pytest

from structured_logger import LoggerConfig, get_logger
from structured_logger.logger import StructuredLogFormatter, _override_langchain_loggers


class TestLangChainLoggerIntegration:
    """Test LangChain logger override functionality."""

    def setup_method(self):
        """Setup for each test method."""
        # Clear any existing LangChain loggers
        langchain_loggers = [
            "langchain",
            "langchain.chains",
            "langchain.agents",
            "langchain.tools",
            "langchain.callbacks",
            "langchain.retrievers",
            "langchain.embeddings",
            "langchain.llms",
            "langchain.chat_models",
        ]
        for logger_name in langchain_loggers:
            logger = logging.getLogger(logger_name)
            logger.handlers.clear()
            logger.setLevel(logging.NOTSET)
            logger.propagate = True

    def test_langchain_logging_disabled_by_default(self):
        """Test that LangChain logging is disabled by default."""
        config = LoggerConfig()
        assert config.enable_langchain_logging is False

    def test_langchain_logging_can_be_enabled(self):
        """Test that LangChain logging can be enabled."""
        config = LoggerConfig(enable_langchain_logging=True)
        assert config.enable_langchain_logging is True

    def test_langchain_loggers_configuration(self):
        """Test LangChain logger configuration."""
        config = LoggerConfig()
        assert "langchain" in config.langchain_loggers
        assert "langchain.chains" in config.langchain_loggers
        assert "langchain.agents" in config.langchain_loggers
        assert "langchain.tools" in config.langchain_loggers

    def test_langchain_log_level_default(self):
        """Test that LangChain log level defaults to WARNING."""
        config = LoggerConfig()
        assert config.langchain_log_level == "WARNING"

    def test_langchain_loggers_silenced_when_disabled(self):
        """Test that LangChain loggers are silenced when disabled."""
        config = LoggerConfig(enable_langchain_logging=False)
        formatter = StructuredLogFormatter(config)

        with patch(
            "structured_logger.logger._is_production_environment", return_value=False
        ):
            _override_langchain_loggers(config, formatter, force_json=True)

        # Check that LangChain loggers are silenced
        for logger_name in config.langchain_loggers:
            logger = logging.getLogger(logger_name)
            # Should be set to CRITICAL+1 which is effectively silent
            assert logger.level > logging.CRITICAL
            assert logger.propagate is False

    def test_langchain_loggers_enabled_when_configured(self):
        """Test that LangChain loggers are enabled when configured."""
        config = LoggerConfig(enable_langchain_logging=True)
        formatter = StructuredLogFormatter(config)

        with patch(
            "structured_logger.logger._is_production_environment", return_value=False
        ):
            _override_langchain_loggers(config, formatter, force_json=True)

        # Check that LangChain loggers have been configured
        for logger_name in config.langchain_loggers:
            logger = logging.getLogger(logger_name)
            assert len(logger.handlers) > 0
            assert logger.level == logging.WARNING
            assert logger.propagate is False

    def test_langchain_logger_structured_formatting(self):
        """Test that LangChain logger uses structured formatting when enabled."""
        config = LoggerConfig(enable_langchain_logging=True)
        formatter = StructuredLogFormatter(config)

        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)

        with patch(
            "structured_logger.logger._is_production_environment", return_value=True
        ):
            _override_langchain_loggers(config, formatter, force_json=True)

        # Get langchain logger and test it
        langchain_logger = logging.getLogger("langchain")
        langchain_logger.handlers.clear()
        langchain_logger.addHandler(handler)
        handler.setFormatter(StructuredLogFormatter(config))

        # Log a message
        langchain_logger.warning("Agent execution started")

        # Get the logged output
        log_output = log_capture.getvalue().strip()

        # Verify it's valid JSON
        try:
            log_data = json.loads(log_output)
            assert log_data["level"] == "WARNING"
            assert log_data["message"] == "Agent execution started"
            assert log_data["module"] == "langchain"
        except json.JSONDecodeError:
            pytest.fail("Log output is not valid JSON")

    def test_langchain_custom_log_level(self):
        """Test that LangChain log level can be customized."""
        config = LoggerConfig(
            enable_langchain_logging=True, langchain_log_level="ERROR"
        )
        formatter = StructuredLogFormatter(config)

        with patch(
            "structured_logger.logger._is_production_environment", return_value=False
        ):
            _override_langchain_loggers(config, formatter, force_json=True)

        # Check that LangChain logger has ERROR level
        langchain_logger = logging.getLogger("langchain")
        assert langchain_logger.level == logging.ERROR

    def test_langchain_logger_with_get_logger(self):
        """Test LangChain logging control via get_logger."""
        # Test with disabled (default)
        config = LoggerConfig(enable_langchain_logging=False)
        logger = get_logger("test_logger_disabled", config=config)

        langchain_logger = logging.getLogger("langchain.chains")
        assert langchain_logger.level > logging.CRITICAL

        # Clear handlers completely for a clean test
        for logger_name in ["test_logger_disabled", "test_logger_enabled"] + list(
            config.langchain_loggers
        ):
            test_logger = logging.getLogger(logger_name)
            test_logger.handlers.clear()
            test_logger.setLevel(logging.NOTSET)
            test_logger.propagate = True

        # Test with enabled using a different logger name
        config = LoggerConfig(enable_langchain_logging=True)
        logger = get_logger("test_logger_enabled", config=config)

        langchain_logger = logging.getLogger("langchain.chains")
        assert langchain_logger.level == logging.WARNING
        assert len(langchain_logger.handlers) > 0

    def test_langchain_chains_logger(self):
        """Test that langchain.chains logger works correctly."""
        config = LoggerConfig(enable_langchain_logging=True, langchain_log_level="INFO")
        formatter = StructuredLogFormatter(config)

        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(StructuredLogFormatter(config))

        with patch(
            "structured_logger.logger._is_production_environment", return_value=True
        ):
            _override_langchain_loggers(config, formatter, force_json=True)

        # Get langchain.chains logger
        chains_logger = logging.getLogger("langchain.chains")
        chains_logger.handlers.clear()
        chains_logger.addHandler(handler)

        # Log a message
        chains_logger.info("[chain/start] Starting chain execution")

        log_output = log_capture.getvalue().strip()

        # Verify it's valid JSON
        try:
            log_data = json.loads(log_output)
            assert log_data["level"] == "INFO"
            assert "[chain/start]" in log_data["message"]
            assert log_data["module"] == "langchain.chains"
        except json.JSONDecodeError:
            pytest.fail("Log output is not valid JSON")

    def test_langchain_logger_prevents_duplicate_logs(self):
        """Test that LangChain loggers don't propagate to prevent duplicates."""
        config = LoggerConfig(enable_langchain_logging=True)
        formatter = StructuredLogFormatter(config)

        with patch(
            "structured_logger.logger._is_production_environment", return_value=True
        ):
            _override_langchain_loggers(config, formatter, force_json=True)

        # Check that all LangChain loggers have propagate=False
        for logger_name in config.langchain_loggers:
            logger = logging.getLogger(logger_name)
            assert logger.propagate is False, f"{logger_name} should not propagate"

    def test_langchain_logger_respects_force_dev(self):
        """Test that LangChain logger override respects force_dev parameter."""
        config = LoggerConfig(enable_langchain_logging=True)
        formatter = StructuredLogFormatter(config)

        with patch(
            "structured_logger.logger._is_production_environment", return_value=True
        ):
            _override_langchain_loggers(config, formatter, force_dev=True)

        # Get langchain logger and check its handler
        langchain_logger = logging.getLogger("langchain")

        # The logger should have handlers with regular formatter when force_dev=True
        assert len(langchain_logger.handlers) > 0
        # Check that the formatter is not a StructuredLogFormatter when force_dev=True
        handler_formatter = langchain_logger.handlers[0].formatter
        assert not isinstance(handler_formatter, StructuredLogFormatter)

    def test_custom_langchain_loggers_list(self):
        """Test that custom LangChain logger list is respected."""
        custom_loggers = ["langchain.chains", "langchain.agents"]
        config = LoggerConfig(
            enable_langchain_logging=True,
            langchain_loggers=custom_loggers,
        )
        formatter = StructuredLogFormatter(config)

        with patch(
            "structured_logger.logger._is_production_environment", return_value=False
        ):
            _override_langchain_loggers(config, formatter, force_json=True)

        # Check that only custom loggers have been configured
        chains_logger = logging.getLogger("langchain.chains")
        assert len(chains_logger.handlers) > 0
        assert chains_logger.propagate is False

        agents_logger = logging.getLogger("langchain.agents")
        assert len(agents_logger.handlers) > 0
        assert agents_logger.propagate is False

        # Check that other langchain loggers are not configured
        tools_logger = logging.getLogger("langchain.tools")
        assert len(tools_logger.handlers) == 0

    def test_langchain_logger_with_extra_fields(self):
        """Test that LangChain loggers support extra fields."""
        config = LoggerConfig(
            enable_langchain_logging=True,
            custom_fields=["request_id", "user_id", "chain_id"],
        )
        formatter = StructuredLogFormatter(config)

        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(StructuredLogFormatter(config))

        with patch(
            "structured_logger.logger._is_production_environment", return_value=True
        ):
            _override_langchain_loggers(config, formatter, force_json=True)

        # Get langchain logger
        langchain_logger = logging.getLogger("langchain")
        langchain_logger.handlers.clear()
        langchain_logger.addHandler(handler)

        # Log with extra fields
        langchain_logger.warning(
            "Agent execution failed",
            extra={
                "request_id": "123",
                "user_id": "456",
                "chain_id": "chain789",
                "error_type": "timeout",
            },
        )

        log_output = log_capture.getvalue().strip()

        # Verify extra fields are included
        try:
            log_data = json.loads(log_output)
            assert log_data["request_id"] == "123"
            assert log_data["user_id"] == "456"
            assert log_data["chain_id"] == "chain789"
            # error_type should be in extra since it's not a custom field
            assert "extra" in log_data
            assert log_data["extra"]["error_type"] == "timeout"
        except json.JSONDecodeError:
            pytest.fail("Log output is not valid JSON")

    def test_langchain_multiline_logs_formatted_as_json(self):
        """Test that multiline LangChain logs are properly formatted as single JSON entries."""
        config = LoggerConfig(enable_langchain_logging=True)
        formatter = StructuredLogFormatter(config)

        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(StructuredLogFormatter(config))

        with patch(
            "structured_logger.logger._is_production_environment", return_value=True
        ):
            _override_langchain_loggers(config, formatter, force_json=True)

        # Get langchain logger
        langchain_logger = logging.getLogger("langchain.chains")
        langchain_logger.handlers.clear()
        langchain_logger.addHandler(handler)

        # Log a multiline message (like LangChain does)
        multiline_message = """[chain/start] Starting AgentExecutor
Input: What is the weather?
Tools: [weather_api, web_search]
Max iterations: 10"""

        langchain_logger.warning(multiline_message)

        log_output = log_capture.getvalue().strip()

        # Verify it's valid JSON (single line)
        try:
            log_data = json.loads(log_output)
            assert log_data["level"] == "WARNING"
            # The entire multiline message should be in the message field
            assert "[chain/start]" in log_data["message"]
            assert "What is the weather?" in log_data["message"]
            # Should be a single JSON object, not multiple lines
            assert log_output.count("\n") == 0 or log_output.count("{") == 1
        except json.JSONDecodeError:
            pytest.fail(f"Log output is not valid JSON: {log_output}")

    def test_langchain_warning_logs_shown_by_default(self):
        """Test that WARNING level LangChain logs are shown by default."""
        config = LoggerConfig(enable_langchain_logging=True)
        formatter = StructuredLogFormatter(config)

        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(StructuredLogFormatter(config))

        with patch(
            "structured_logger.logger._is_production_environment", return_value=True
        ):
            _override_langchain_loggers(config, formatter, force_json=True)

        # Get langchain logger
        langchain_logger = logging.getLogger("langchain")
        langchain_logger.handlers.clear()
        langchain_logger.addHandler(handler)

        # Try to log INFO message (should be filtered out)
        langchain_logger.info("This should not appear")

        # Try to log WARNING message (should appear)
        langchain_logger.warning("This should appear")

        log_output = log_capture.getvalue().strip()

        # Should only contain the WARNING message
        assert "This should not appear" not in log_output
        assert "This should appear" in log_output
