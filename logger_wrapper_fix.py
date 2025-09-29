"""
Temporary wrapper to handle invalid 'error' keyword arguments.
This is a workaround - you should fix the actual problematic logger calls instead.
"""

import logging
from functools import wraps
from typing import Any


def create_safe_logger_wrapper(logger):
    """
    Create a wrapper that handles invalid 'error' keyword arguments.

    WARNING: This is a temporary workaround. You should fix the actual
    problematic logger calls instead of using this wrapper.
    """

    class SafeLoggerWrapper:
        def __init__(self, wrapped_logger):
            self._logger = wrapped_logger

        def __getattr__(self, name):
            attr = getattr(self._logger, name)
            if callable(attr) and name in [
                "debug",
                "info",
                "warning",
                "error",
                "critical",
                "exception",
            ]:
                return self._wrap_log_method(attr)
            return attr

        def _wrap_log_method(self, method):
            @wraps(method)
            def wrapper(*args, **kwargs):
                # Handle invalid 'error' keyword argument
                if "error" in kwargs:
                    error_value = kwargs.pop("error")
                    # Move it to extra if extra exists, otherwise create extra
                    if "extra" not in kwargs:
                        kwargs["extra"] = {}
                    kwargs["extra"]["error"] = str(error_value)

                return method(*args, **kwargs)

            return wrapper

    return SafeLoggerWrapper(logger)


# Example usage (add this to your main.py temporarily):
"""
from structured_logger import get_logger
from logger_wrapper_fix import create_safe_logger_wrapper

# Instead of:
# logger = get_logger(__name__)

# Use:
logger = create_safe_logger_wrapper(get_logger(__name__))
"""
