from unittest.mock import Mock, patch

from bot.modules.client.API.weather import OpenWeather
from bot.Settings.settings import Settings


@patch("bot.modules.client.API.weather.requests.get")
def test_get_weather_uses_geocoded_coordinates(mock_get):
    geocoding_response = Mock()
    geocoding_response.json.return_value = [{"lat": 55.6761, "lon": 12.5683}]
    weather_response = Mock()
    weather_response.json.return_value = {"main": {"temp": 20}}
    mock_get.side_effect = [geocoding_response, weather_response]

    settings = Settings(
        discord_token="test-token",
        openai_api_key="test-openai-key",
        openweather_api_key="test-api-key",
    )
    weather = OpenWeather("Copenhagen", "", "DK", settings=settings)
    result = weather.get_weather()

    assert result == {"main": {"temp": 20}}
    assert mock_get.call_count == 2
    geocoding_response.raise_for_status.assert_called_once_with()
    weather_response.raise_for_status.assert_called_once_with()
