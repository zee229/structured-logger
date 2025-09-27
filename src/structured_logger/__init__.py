"""
Structured JSON logger for Python applications with flexible configuration.

A powerful, configurable logging library that outputs structured JSON logs,
perfect for cloud deployments, containerized applications, and log aggregation systems.
"""

from .logger import LoggerConfig, StructuredLogFormatter, get_logger, setup_root_logger

# Import advanced features if available
try:
    from .advanced import (
        AdvancedStructuredFormatter,
        AsyncLogger,
        AsyncLogHandler,
        CorrelationIDManager,
        LogMetrics,
        LogSchema,
        LogValidator,
        MetricsConfig,
        RateLimiter,
        RotationConfig,
        SamplingConfig,
        StructuredRotatingFileHandler,
        StructuredTimedRotatingFileHandler,
    )

    ADVANCED_FEATURES_AVAILABLE = True
except ImportError:
    ADVANCED_FEATURES_AVAILABLE = False

# Import Sentry integration if available
try:
    from .sentry_integration import (
        SentryConfig,
        SentryLogHandler,
        add_sentry_breadcrumb,
        capture_exception_with_context,
        capture_message_with_context,
        initialize_sentry,
        is_sentry_available,
        is_sentry_initialized,
        set_sentry_context,
        set_sentry_user,
    )

    SENTRY_INTEGRATION_AVAILABLE = True
except ImportError:
    SENTRY_INTEGRATION_AVAILABLE = False

__version__ = "1.2.0"
__author__ = "Nikita Yastreb"
__email__ = "yastrebnikita723@gmail.com"

__all__ = [
    "StructuredLogFormatter",
    "get_logger",
    "setup_root_logger",
    "LoggerConfig",
]

# Add advanced features to exports if available
if ADVANCED_FEATURES_AVAILABLE:
    __all__.extend(
        [
            "LogSchema",
            "SamplingConfig",
            "MetricsConfig",
            "RotationConfig",
            "LogValidator",
            "RateLimiter",
            "LogMetrics",
            "CorrelationIDManager",
            "AsyncLogHandler",
            "StructuredRotatingFileHandler",
            "StructuredTimedRotatingFileHandler",
            "AdvancedStructuredFormatter",
            "AsyncLogger",
        ]
    )

# Add Sentry integration to exports if available
if SENTRY_INTEGRATION_AVAILABLE:
    __all__.extend(
        [
            "SentryConfig",
            "SentryLogHandler",
            "initialize_sentry",
            "capture_exception_with_context",
            "capture_message_with_context",
            "add_sentry_breadcrumb",
            "set_sentry_user",
            "set_sentry_context",
            "is_sentry_available",
            "is_sentry_initialized",
        ]
    )
