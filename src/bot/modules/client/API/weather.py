from typing import Any
from urllib.parse import quote

import requests

from .api_client import ApiClient


class OpenWeather(ApiClient):
    API_KEY_ENV_VAR = "OPENWEATHER_API_KEY"
    DIRECT_GEOCODING_ENDPOINT = "https://api.openweathermap.org/geo/1.0/direct"
    CURRENT_WEATHER_ENDPOINT = "https://api.openweathermap.org/data/2.5/weather"

    def __init__(self, city_name: str, state_code: str, country_code: str):
        self.city_name = city_name
        self.state_code = state_code
        self.country_code = country_code

    def get_geocoding(self, limit: int = 1) -> list[dict[str, Any]]:
        if not 1 <= limit <= 5:
            raise ValueError("limit must be between 1 and 5")

        location = (
            f"{self.city_name.strip()},"
            f"{self.state_code.strip()},"
            f"{self.country_code.strip()}"
        )

        base_url = (
            f"{self.DIRECT_GEOCODING_ENDPOINT}"
            f"?q={quote(location, safe=',')}"
            f"&limit={limit}"
            f"&appid={quote(self.get_api_key(), safe='')}"
        )
        response = requests.get(base_url, timeout=15)
        response.raise_for_status()
        return response.json()

    def get_weather(self) -> dict[str, Any]:
        """Return current weather for the first geocoding match."""
        locations = self.get_geocoding()
        if not locations:
            raise LookupError(
                f"No location found for {self.city_name}, {self.country_code}"
            )

        first_location = locations[0]
        latitude = first_location["lat"]
        longitude = first_location["lon"]

        weather_url = (
            f"{self.CURRENT_WEATHER_ENDPOINT}"
            f"?lat={latitude}"
            f"&lon={longitude}"
            f"&units=metric"
            f"&appid={quote(self.get_api_key(), safe='')}"
        )
        response = requests.get(weather_url, timeout=15)
        response.raise_for_status()
        return response.json()
