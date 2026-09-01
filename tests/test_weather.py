from unittest.mock import Mock, patch

from bot.modules.client.API.weather import OpenWeather


@patch("bot.modules.client.API.weather.requests.get")
def test_get_weather_uses_geocoded_coordinates(mock_get):
    geocoding_response = Mock()
    geocoding_response.json.return_value = [{"lat": 55.6761, "lon": 12.5683}]
    weather_response = Mock()
    weather_response.json.return_value = {"main": {"temp": 20}}
    mock_get.side_effect = [geocoding_response, weather_response]

    weather = OpenWeather("Copenhagen", "", "DK")
    with patch.object(weather, "get_api_key", return_value="test-api-key"):
        result = weather.get_weather()

    assert result == {"main": {"temp": 20}}
    assert mock_get.call_count == 2
    geocoding_response.raise_for_status.assert_called_once_with()
    weather_response.raise_for_status.assert_called_once_with()
