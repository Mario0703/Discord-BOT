import pytest

from bot.errors import MissingConfigurationError, OptionalFeatureUnavailableError
from bot.modules.client.API.is_there_such_deal import Deals
from bot.modules.client.API.weather import OpenWeather
from bot.modules.client.ElevenLabs.elevenlabs import ElevenLabsClient
from bot.modules.client.openAI.orchestration import OpenAIGateway
from bot.Settings.settings import Settings


def _settings(**overrides) -> Settings:
    values = {
        "discord_token": "test-token",
        "openai_api_key": "test-openai-key",
    }
    values.update(overrides)
    return Settings(**values)


def test_openai_reports_missing_required_api_key():
    with pytest.raises(
        MissingConfigurationError,
        match="OpenAI API key is required.",
    ):
        OpenAIGateway(settings=_settings(openai_api_key=""))


@pytest.mark.parametrize(
    ("use_feature", "message"),
    [
        (
            lambda: ElevenLabsClient(settings=_settings()).convert_text_to_speech(
                "Hello"
            ),
            "ElevenLabs speech is unavailable",
        ),
        (
            lambda: OpenWeather("Copenhagen", "", "DK", settings=_settings()),
            "Weather is unavailable",
        ),
        (
            lambda: Deals("DK", 61, (80, 100), settings=_settings()),
            "Deals are unavailable",
        ),
    ],
)
def test_optional_features_report_missing_api_keys(use_feature, message):
    with pytest.raises(OptionalFeatureUnavailableError, match=message):
        use_feature()
