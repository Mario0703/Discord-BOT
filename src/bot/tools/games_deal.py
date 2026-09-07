import asyncio

from bot.settings.settings import Settings

from ..modules.client.api.is_there_such_deal import IsThereAnyDealClient
from .tool import Tool


class GamesDealTool(Tool):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.name = "get_game_deals"
        self.description = "Find game deals from IsThereAnyDeal."
        self.parameters = {
            "type": "object",
            "properties": {
                "country": {
                    "type": "string",
                    "description": "ISO country code, e.g. DK.",
                },
                "shop": {
                    "type": "integer",
                    "description": "IsThereAnyDeal shop ID, e.g. 61 for Steam.",
                },
                "discount_min": {
                    "type": "integer",
                    "description": "Minimum discount percentage (0-100).",
                },
                "discount_max": {
                    "type": "integer",
                    "description": "Maximum discount percentage (0-100).",
                },
            },
            "required": ["country", "shop", "discount_min", "discount_max"],
            "additionalProperties": False,
        }

    async def execute(self, **kwargs: object) -> dict[str, object]:
        deals = IsThereAnyDealClient(
            country=self.string_argument(kwargs, "country"),
            shop=self.integer_argument(kwargs, "shop"),
            discount_range=(
                self.integer_argument(kwargs, "discount_min"),
                self.integer_argument(kwargs, "discount_max"),
            ),
            settings=self.settings,
        )
        return await asyncio.to_thread(deals.get_steam_deals)
