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

__version__ = "1.0.0"
__author__ = "Nikita Yastreb"
__email__ = "yastrebnikita723@gmail.com"

__all__ = [
    "StructuredLogFormatter",
    "get_logger", 
    "setup_root_logger",
    "LoggerConfig",
]