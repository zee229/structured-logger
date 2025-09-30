"""
Test that logs are written to stdout instead of stderr.

This is important for Railway compatibility, as Railway treats
anything written to stderr as an error.
"""

import io
import logging
import os
from contextlib import redirect_stderr, redirect_stdout

from structured_logger import LoggerConfig, get_logger, setup_root_logger


class TestStdoutOutput:
    """Test that all logs go to stdout, not stderr."""

    def test_logger_writes_to_stdout_not_stderr(self):
        """Test that get_logger writes to stdout."""
        # Set production environment
        os.environ["RAILWAY_ENVIRONMENT"] = "production"

        # Create string buffers to capture output
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()

        # Create logger with JSON format
        config = LoggerConfig()

        # Redirect stdout and stderr
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            logger = get_logger("test.stdout", config=config, force_json=True)
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")

        # Get the output
        stdout_output = stdout_buffer.getvalue()
        stderr_output = stderr_buffer.getvalue()

        # Verify all logs went to stdout
        assert "Info message" in stdout_output
        assert "Warning message" in stdout_output
        assert "Error message" in stdout_output

        # Verify stderr is empty (or only contains non-log output)
        # Note: stderr might have some pytest/test framework output
        assert "Info message" not in stderr_output
        assert "Warning message" not in stderr_output
        assert "Error message" not in stderr_output

        # Clean up
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        del os.environ["RAILWAY_ENVIRONMENT"]

    def test_root_logger_writes_to_stdout(self):
        """Test that setup_root_logger writes to stdout."""
        # Set production environment
        os.environ["RAILWAY_ENVIRONMENT"] = "production"

        # Create string buffers
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()

        # Setup root logger
        config = LoggerConfig()

        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            setup_root_logger(config=config, force_json=True)
            root_logger = logging.getLogger()
            root_logger.info("Root info message")
            root_logger.error("Root error message")

        stdout_output = stdout_buffer.getvalue()
        stderr_output = stderr_buffer.getvalue()

        # Verify logs went to stdout
        assert "Root info message" in stdout_output
        assert "Root error message" in stdout_output

        # Verify stderr is empty
        assert "Root info message" not in stderr_output
        assert "Root error message" not in stderr_output

        # Clean up
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        del os.environ["RAILWAY_ENVIRONMENT"]

    def test_dev_format_writes_to_stdout(self):
        """Test that development format also writes to stdout."""
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()

        config = LoggerConfig()

        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            logger = get_logger("test.dev", config=config, force_dev=True)
            logger.info("Dev format info")
            logger.error("Dev format error")

        stdout_output = stdout_buffer.getvalue()
        stderr_output = stderr_buffer.getvalue()

        # Verify logs went to stdout
        assert "Dev format info" in stdout_output
        assert "Dev format error" in stdout_output

        # Verify stderr is empty
        assert "Dev format info" not in stderr_output
        assert "Dev format error" not in stderr_output

        # Clean up
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

    def test_json_output_contains_correct_level(self):
        """Test that JSON output contains the correct log level."""
        os.environ["RAILWAY_ENVIRONMENT"] = "production"
        stdout_buffer = io.StringIO()

        config = LoggerConfig()

        with redirect_stdout(stdout_buffer):
            logger = get_logger("test.level", config=config, force_json=True)
            logger.info("Info level test")
            logger.warning("Warning level test")
            logger.error("Error level test")

        stdout_output = stdout_buffer.getvalue()

        # Verify correct levels in JSON output
        assert '"level": "INFO"' in stdout_output
        assert '"level": "WARNING"' in stdout_output
        assert '"level": "ERROR"' in stdout_output

        # Verify no incorrect level assignments
        lines = stdout_output.strip().split("\n")
        for line in lines:
            if "Info level test" in line:
                assert '"level": "INFO"' in line
                assert '"level": "ERROR"' not in line
            elif "Warning level test" in line:
                assert '"level": "WARNING"' in line
                assert '"level": "ERROR"' not in line
            elif "Error level test" in line:
                assert '"level": "ERROR"' in line
                assert '"level": "INFO"' not in line

        # Clean up
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        del os.environ["RAILWAY_ENVIRONMENT"]

    def test_railway_compatibility(self):
        """
        Test that logs are Railway-compatible.

        Railway treats stderr as errors, so all logs must go to stdout
        with proper level fields in the JSON.
        """
        os.environ["RAILWAY_ENVIRONMENT"] = "production"
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()

        config = LoggerConfig()

        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            logger = get_logger("app.db.mongo", config=config, force_json=True)
            # Simulate the exact log from the Railway screenshot
            logger.info("Creating new MongoDB client connection")

        stdout_output = stdout_buffer.getvalue()
        stderr_output = stderr_buffer.getvalue()

        # Verify the log went to stdout
        assert "Creating new MongoDB client connection" in stdout_output
        assert '"level": "INFO"' in stdout_output
        assert '"module": "app.db.mongo"' in stdout_output

        # Verify stderr is empty (Railway won't see this as an error)
        assert "Creating new MongoDB client connection" not in stderr_output

        # Clean up
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        del os.environ["RAILWAY_ENVIRONMENT"]
