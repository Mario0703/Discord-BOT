import pytest

from bot.Settings.settings import Settings, _check_api_keys_settings


def test_missing_optional_api_keys_warn_without_stopping_startup():
    settings = Settings(
        discord_token="test-token",
        openai_api_key="test-openai-key",
    )

    with pytest.warns(RuntimeWarning, match="3 optional API key"):
        configured = _check_api_keys_settings(settings)

    assert configured is False


def test_configured_optional_api_keys_do_not_warn():
    settings = Settings(
        discord_token="test-token",
        openai_api_key="test-openai-key",
        elevenlabs_api_key="elevenlabs-key",
        itad_api_key="itad-key",
        openweather_api_key="weather-key",
    )

    assert _check_api_keys_settings(settings) is True
