from pathlib import Path

import pytest

from bot.errors import ConfigurationError
from bot.Settings.settings import (
    Settings,
    _check_api_keys_settings,
    load_settings,
)


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


@pytest.mark.parametrize(
    "field_name",
    [
        "summary_max_days",
        "summary_max_messages",
        "summary_max_characters",
        "upload_max_bytes",
        "tts_max_characters",
        "max_tool_calls",
    ],
)
def test_numeric_limits_must_be_positive(field_name):
    with pytest.raises(ConfigurationError, match="must be greater than zero"):
        Settings(
            discord_token="test-token",
            openai_api_key="test-openai-key",
            **{field_name: 0},
        )


def test_default_openai_model_must_be_supported():
    with pytest.raises(ConfigurationError, match="Unsupported OpenAI model"):
        Settings(
            discord_token="test-token",
            openai_api_key="test-openai-key",
            openai_model="unsupported-model",
        )


def test_default_reasoning_level_must_be_supported_by_model():
    with pytest.raises(ConfigurationError, match="Reasoning level"):
        Settings(
            discord_token="test-token",
            openai_api_key="test-openai-key",
            openai_model="gpt-5",
            openai_reasoning_level="xhigh",
        )


def test_load_settings_reads_optional_configuration_overrides(monkeypatch):
    environment = {
        "TOKEN": "discord-token",
        "GUILD_IDS": "123,456",
        "OPENAI_API_KEY": "openai-key",
        "OPENAI_MODEL": "gpt-5",
        "OPENAI_REASONING_LEVEL": "high",
        "DATA_DIR": "custom-data",
        "SUMMARY_MAX_DAYS": "3",
        "SUMMARY_MAX_MESSAGES": "200",
        "SUMMARY_MAX_CHARACTERS": "3000",
        "UPLOAD_MAX_BYTES": "4000",
        "TTS_MAX_CHARACTERS": "500",
        "MAX_TOOL_CALLS": "2",
    }
    for name, value in environment.items():
        monkeypatch.setenv(name, value)

    settings = load_settings()

    assert settings.guild_ids == (123, 456)
    assert settings.openai_model == "gpt-5"
    assert settings.openai_reasoning_level == "high"
    assert settings.data_dir == Path("custom-data")
    assert settings.summary_max_days == 3
    assert settings.summary_max_messages == 200
    assert settings.summary_max_characters == 3000
    assert settings.upload_max_bytes == 4000
    assert settings.tts_max_characters == 500
    assert settings.max_tool_calls == 2
