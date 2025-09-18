"""
Structured JSON logger for Python applications with flexible configuration.

A powerful, configurable logging library that outputs structured JSON logs,
perfect for cloud deployments, containerized applications, and log aggregation systems.
"""

from .logger import (
    StructuredLogFormatter,
    get_logger,
    setup_root_logger,
    LoggerConfig,
)

# Import advanced features if available
try:
    from .advanced import (
        LogSchema,
        SamplingConfig,
        MetricsConfig,
        RotationConfig,
        LogValidator,
        RateLimiter,
        LogMetrics,
        CorrelationIDManager,
        AsyncLogHandler,
        StructuredRotatingFileHandler,
        StructuredTimedRotatingFileHandler,
        AdvancedStructuredFormatter,
        AsyncLogger
    )
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError:
    ADVANCED_FEATURES_AVAILABLE = False

__version__ = "1.1.0"
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
    __all__.extend([
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
        "AsyncLogger"
    ])