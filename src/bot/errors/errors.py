"""Application exceptions and safe user-facing error messages."""


class ConfigurationError(RuntimeError):
    """Raised when required application configuration is invalid or missing."""
    pass


class OptionalFeatureUnavailableError(RuntimeError):
    """Raised when an optional feature is not configured or available."""
    pass


class MissingConfigurationError(ConfigurationError):
    """Raised when a required configuration is missing."""
    pass


class Errors:
    """Build consistent, safe messages for errors shown to Discord users."""

    @staticmethod
    def missing_configuration(variable_name: str) -> str:
        return (
            f"The bot is missing required configuration for `{variable_name}`. "
            "Please contact an administrator."
        )

    @staticmethod
    def feature_unavailable(feature_name: str) -> str:
        return (
            f"The {feature_name} feature is currently unavailable because it "
            "has not been configured."
        )

    @staticmethod
    def operation_failed(operation: str) -> str:
        return f"I could not complete the {operation}. " "Please try again later."

    @staticmethod
    def invalid_input(message: str) -> str:
        return f"Invalid input: {message}"
