"""
Test environment configuration and .env file loading.
"""

import os

import pytest

from structured_logger import LoggerConfig, SentryConfig, get_logger


class TestEnvironmentConfiguration:
    """Test environment variable configuration."""

    def test_env_vars_loaded(self, test_env_vars):
        """Test that environment variables are loaded correctly."""
        assert test_env_vars["environment"] == "test"
        assert test_env_vars["testing"] is True
        assert test_env_vars["log_level"] in ["DEBUG", "INFO", "WARNING", "ERROR"]
        assert test_env_vars["test_user_id"] is not None

    def test_logger_with_env_config(self, test_env_vars, logger_test_config):
        """Test logger creation using environment configuration."""
        logger = get_logger("env_test", config=logger_test_config)

        # Test logging with environment-based test data
        logger.info(
            "Environment test message",
            extra={
                "user_id": test_env_vars["test_user_id"],
                "company_id": test_env_vars["test_company_id"],
                "request_id": test_env_vars["test_request_id"],
                "environment": test_env_vars["environment"],
            },
        )

        assert logger is not None
        assert len(logger.handlers) > 0

    @pytest.mark.sentry
    def test_sentry_config_from_env(self, test_env_vars, real_sentry_available):
        """Test Sentry configuration from environment variables."""
        if not real_sentry_available:
            pytest.skip("Real Sentry DSN not available")

        import logging

        sentry_config = SentryConfig(
            dsn=test_env_vars["sentry_dsn"],
            min_level=getattr(logging, test_env_vars["log_level"]),
            environment=test_env_vars["environment"],
            tag_fields=["user_id", "company_id", "request_id"],
        )

        logger_config = LoggerConfig(
            enable_sentry=True,
            sentry_config=sentry_config,
            custom_fields=["user_id", "company_id", "request_id"],
        )

        logger = get_logger("sentry_env_test", config=logger_config)
        assert logger is not None

    def test_fallback_values(self):
        """Test that fallback values work when env vars are not set."""
        # Test with non-existent env var
        value = os.getenv("NON_EXISTENT_VAR", "fallback_value")
        assert value == "fallback_value"

    @pytest.mark.integration
    def test_full_integration_with_env(self, test_env_vars, sample_log_data):
        """Test full logging integration using environment configuration."""
        config = LoggerConfig(
            enable_sentry=False,  # Disable for this test
            custom_fields=["user_id", "company_id", "request_id"],
        )

        logger = get_logger("integration_test", config=config, force_json=True)

        # Log with environment-based test data
        logger.info("Integration test message", extra=sample_log_data)
        logger.error("Integration test error", extra=sample_log_data)

        assert logger is not None


class TestEnvironmentSpecificBehavior:
    """Test behavior that changes based on environment."""

    def test_test_environment_behavior(self, test_env_vars):
        """Test behavior specific to test environment."""
        if test_env_vars["environment"] == "test":
            # In test environment, we might want different behavior
            assert test_env_vars["testing"] is True

            # Test-specific logger configuration
            config = LoggerConfig(
                enable_sentry=False,  # Always disabled in tests
                custom_fields=["user_id", "request_id"],
            )

            logger = get_logger("test_specific", config=config)
            logger.debug("This is a test-only debug message")

            assert logger is not None

    def test_production_like_behavior(self, mock_sentry_dsn):
        """Test production-like behavior with mocked services."""
        # Simulate production environment
        os.environ["ENVIRONMENT"] = "production"
        os.environ["SENTRY_DSN"] = mock_sentry_dsn

        try:
            import logging

            sentry_config = SentryConfig(
                dsn=mock_sentry_dsn,
                min_level=logging.ERROR,  # Only errors in production
                environment="production",
            )

            config = LoggerConfig(
                enable_sentry=True,
                sentry_config=sentry_config,
            )

            logger = get_logger("production_test", config=config)
            assert logger is not None

        finally:
            # Clean up
            os.environ.pop("ENVIRONMENT", None)
            os.environ.pop("SENTRY_DSN", None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
