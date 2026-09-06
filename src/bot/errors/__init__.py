"""Shared application errors and user-facing error messages."""

from .errors import (
    ConfigurationError,
    Errors,
    MissingConfigurationError,
    OptionalFeatureUnavailableError,
)

__all__ = [
    "ConfigurationError",
    "Errors",
    "MissingConfigurationError",
    "OptionalFeatureUnavailableError",
]
