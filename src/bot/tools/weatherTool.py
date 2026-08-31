from typing import Any

from .tool import tool
from ..modules.client.API.weather import OpenWeather


class WeatherTool(tool):
    def __init__(self):
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
                    "description": "State code, for example CA. Use an empty string if unavailable.",
                },
                "country_code": {
                    "type": "string",
                    "description": "Two-letter ISO country code, for example DK.",
                },
            },
            "required": ["city_name", "state_code", "country_code"],
            "additionalProperties": False,
        }

    def definition(self) -> dict[str, Any]:
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        weather = OpenWeather(
            city_name=kwargs["city_name"],
            state_code=kwargs["state_code"],
            country_code=kwargs["country_code"],
        )
        return weather.get_weather()
