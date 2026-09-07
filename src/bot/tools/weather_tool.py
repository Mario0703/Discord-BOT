import asyncio

from bot.settings.settings import Settings

from ..modules.client.api.weather import OpenWeather
from .tool import Tool


class WeatherTool(Tool):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.name = "get_current_weather"
        self.description = (
            "Get current weather for a city using its city, optional state, "
            "and ISO country code."
        )
        self.parameters = {
            "type": "object",
            "properties": {
                "city_name": {
                    "type": "string",
                    "description": "City name, for example Copenhagen.",
                },
                "state_code": {
                    "type": "string",
                    "description": (
                        "State code, for example CA. Use an empty string if "
                        "unavailable."
                    ),
                },
                "country_code": {
                    "type": "string",
                    "description": "Two-letter ISO country code, for example DK.",
                },
            },
            "required": ["city_name", "state_code", "country_code"],
            "additionalProperties": False,
        }

    async def execute(self, **kwargs: object) -> dict[str, object]:
        weather = OpenWeather(
            city_name=self.string_argument(kwargs, "city_name"),
            state_code=self.string_argument(kwargs, "state_code"),
            country_code=self.string_argument(kwargs, "country_code"),
            settings=self.settings,
        )
        return await asyncio.to_thread(weather.get_weather)
