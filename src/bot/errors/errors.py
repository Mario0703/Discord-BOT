"""Application exceptions and safe user-facing error messages."""


class ApplicationError(RuntimeError):
    """An expected failure with a message safe for users and tool results."""


class InvalidInput(ApplicationError, ValueError):
    """The supplied arguments are invalid."""


class AccessDenied(ApplicationError):
    """The caller lacks permission to perform this operation."""


class ResourceNotFound(ApplicationError, LookupError):
    """The requested resource does not exist."""


class ExternalServiceUnavailable(ApplicationError):
    """A provider could not complete the request."""


class ConfigurationError(ApplicationError):
    """Raised when required application configuration is invalid or missing."""

    pass


class OptionalFeatureUnavailableError(ExternalServiceUnavailable):
    """Raised when an optional feature is not configured or available."""

    pass


class MissingConfigurationError(ConfigurationError):
    """Raised when a required configuration is missing."""

    pass


class ToolCallLimitError(InvalidInput):
    """Raised when an OpenAI response exceeds the configured tool-call limit."""
