"""Shared application errors and user-facing error messages."""

from .errors import (
    ConfigurationError,
    Errors,
    MissingConfigurationError,
    OptionalFeatureUnavailableError,
    ToolCallLimitError,
)

__all__ = [
    "ConfigurationError",
    "Errors",
    "MissingConfigurationError",
    "OptionalFeatureUnavailableError",
    "ToolCallLimitError",
]
