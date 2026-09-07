"""Shared application errors and user-facing error messages."""

from .errors import (
    AccessDenied,
    ApplicationError,
    ConfigurationError,
    ExternalServiceUnavailable,
    InvalidInput,
    MissingConfigurationError,
    OptionalFeatureUnavailableError,
    ResourceNotFound,
    ToolCallLimitError,
)

__all__ = [
    "AccessDenied",
    "ApplicationError",
    "ExternalServiceUnavailable",
    "InvalidInput",
    "ResourceNotFound",
    "ConfigurationError",
    "MissingConfigurationError",
    "OptionalFeatureUnavailableError",
    "ToolCallLimitError",
]
