from typing import Any

from .tool import tool
from ..modules.client.API.isThereSuchDeal import Deals


class GamesDealTool(tool):
    def __init__(self):
        self.name = "get_game_deals"
        self.description = "Find game deals from IsThereAnyDeal."
        self.parameters = {
            "type": "object",
            "properties": {
                "country": {"type": "string", "description": "ISO country code, e.g. DK."},
                "shop": {"type": "integer", "description": "IsThereAnyDeal shop ID, e.g. 61 for Steam."},
                "discount_min": {"type": "integer", "description": "Minimum discount percentage (0-100)."},
                "discount_max": {"type": "integer", "description": "Maximum discount percentage (0-100)."},
            },
            "required": ["country", "shop", "discount_min", "discount_max"],
            "additionalProperties": False,
        }

    def definition(self) -> dict[str, Any]:
        return {"type": "function", "name": self.name, "description": self.description, "parameters": self.parameters}

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        deals = Deals(
            country=kwargs["country"],
            shop=kwargs["shop"],
            discount_range=(kwargs["discount_min"], kwargs["discount_max"]),
        )
        return deals.get_steam_deals()
