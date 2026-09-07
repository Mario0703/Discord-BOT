from urllib.parse import quote

import requests

from bot.errors import (
    ExternalServiceUnavailable,
    InvalidInput,
    MissingConfigurationError,
    OptionalFeatureUnavailableError,
    ResourceNotFound,
)
from bot.settings.settings import Settings

from .payloads import object_list, object_payload


class OpenWeather:
    DIRECT_GEOCODING_ENDPOINT = "https://api.openweathermap.org/geo/1.0/direct"
    CURRENT_WEATHER_ENDPOINT = "https://api.openweathermap.org/data/2.5/weather"

    def __init__(
        self,
        city_name: str,
        state_code: str,
        country_code: str,
        settings: Settings | None = None,
    ) -> None:
        if settings is None:
            raise MissingConfigurationError("Settings are required.")
        if not settings.openweather_api_key:
            raise OptionalFeatureUnavailableError(
                "Weather is unavailable because OPENWEATHER_API_KEY is not configured."
            )

        if not city_name.strip() or not country_code.strip():
            raise InvalidInput("City and country must be specified.")
        self.city_name = city_name
        self.state_code = state_code
        self.country_code = country_code
        self.api_key = settings.openweather_api_key

    def get_geocoding(self, limit: int = 1) -> list[dict[str, object]]:
        if not 1 <= limit <= 5:
            raise InvalidInput("limit must be between 1 and 5")

        location = (
            f"{self.city_name.strip()},"
            f"{self.state_code.strip()},"
            f"{self.country_code.strip()}"
        )

        base_url = (
            f"{self.DIRECT_GEOCODING_ENDPOINT}"
            f"?q={quote(location, safe=',')}"
            f"&limit={limit}"
            f"&appid={quote(self.api_key or '', safe='')}"
        )
        try:
            response = requests.get(base_url, timeout=15)
            response.raise_for_status()
            return object_list(response.json())
        except (requests.RequestException, ValueError) as error:
            raise ExternalServiceUnavailable(
                "Weather is temporarily unavailable."
            ) from error

    def get_weather(self) -> dict[str, object]:
        """Return current weather for the first geocoding match."""
        locations = self.get_geocoding()
        if not locations:
            raise ResourceNotFound(
                f"No location found for {self.city_name}, {self.country_code}"
            )

        first_location = locations[0]
        latitude = first_location.get("lat")
        longitude = first_location.get("lon")
        if any(
            isinstance(value, bool) or not isinstance(value, (int, float))
            for value in (latitude, longitude)
        ):
            raise ExternalServiceUnavailable("Weather returned invalid coordinates.")

        weather_url = (
            f"{self.CURRENT_WEATHER_ENDPOINT}"
            f"?lat={latitude}"
            f"&lon={longitude}"
            f"&units=metric"
            f"&appid={quote(self.api_key or '', safe='')}"
        )
        try:
            response = requests.get(weather_url, timeout=15)
            response.raise_for_status()
            return object_payload(response.json())
        except (requests.RequestException, ValueError) as error:
            raise ExternalServiceUnavailable(
                "Weather is temporarily unavailable."
            ) from error
