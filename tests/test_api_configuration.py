from unittest.mock import Mock

import pytest

from bot.errors import MissingConfigurationError
from bot.modules.client.API.is_there_such_deal import Deals
from bot.modules.client.API.weather import OpenWeather
from bot.modules.client.ElevenLabs.elevenlabs import ElevenLabsClient
from bot.modules.client.openAI.openai_client_impl import OpenAiCLientImpl
from bot.Settings.settings import Settings


def _settings(**overrides) -> Settings:
    values = {
        "discord_token": "test-token",
        "openai_api_key": "test-openai-key",
    }
    values.update(overrides)
    return Settings(**values)


@pytest.mark.parametrize(
    ("create_client", "message"),
    [
        (
            lambda: OpenAiCLientImpl(
                client=Mock(),
                settings=_settings(openai_api_key=""),
            ),
            "OpenAI API key is required.",
        ),
        (
            lambda: ElevenLabsClient(settings=_settings()),
            "ElevenLabs API key is required.",
        ),
        (
            lambda: OpenWeather("Copenhagen", "", "DK", settings=_settings()),
            "OpenWeather API key is required.",
        ),
        (
            lambda: Deals("DK", 61, (80, 100), settings=_settings()),
            "IsThereAnyDeal API key is required.",
        ),
    ],
)
def test_clients_report_missing_api_keys(create_client, message):
    with pytest.raises(MissingConfigurationError, match=message):
        create_client()
