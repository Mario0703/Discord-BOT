from bot.errors import (
    ConfigurationError,
    Errors,
    OptionalFeatureUnavailableError,
)


def test_errors_create_safe_user_messages():
    assert "OPENAI_API_KEY" in Errors.missing_configuration("OPENAI_API_KEY")
    assert "weather" in Errors.feature_unavailable("weather")
    assert "try again later" in Errors.operation_failed("transcription")
    assert Errors.invalid_input("bad date") == "Invalid input: bad date"


def test_custom_errors_are_runtime_errors():
    assert issubclass(ConfigurationError, RuntimeError)
    assert issubclass(OptionalFeatureUnavailableError, RuntimeError)
