from datetime import datetime
from typing import Any

from bot.tools.games_deal import GamesDealTool

from ..orchestration import AssistantService
from .prompts import ranking_prompt


class TopDealsService:
    """Fetch and present the three strongest current Steam deals."""

    def __init__(self, assistant_service: AssistantService, deals_tool: GamesDealTool):
        self.assistant_service = assistant_service
        self.deals_tool = deals_tool

    async def get_top_steam_deals(
        self,
        user_id: str | int,
        country: str = "DK",
        minimum_discount: int = 80,
        maximum_discount: int = 80,
        steam_store: int = 61,
    ) -> str:
        raw_deals = await self.deals_tool.execute(
            country=country,
            shop=steam_store,
            discount_min=minimum_discount,
            discount_max=maximum_discount,
        )

        prompt = ranking_prompt(self._normalise_deals(raw_deals))
        return await self.assistant_service.get_stateless_response(prompt, user_id)

    @staticmethod
    def _normalise_deals(raw_deals: dict[str, Any]) -> list[dict[str, Any]]:
        deals_for_ai = []

        for item in raw_deals.get("list", []):
            deal = item.get("deal", {})
            expiry = deal.get("expiry")

            deals_for_ai.append(
                {
                    "title": item.get("title"),
                    "store": deal.get("shop", {}).get("name"),
                    "current_price": deal.get("price", {}).get("amount"),
                    "regular_price": deal.get("regular", {}).get("amount"),
                    "currency": deal.get("price", {}).get("currency"),
                    "discount_percent": deal.get("cut"),
                    "platforms": [
                        platform.get("name")
                        for platform in deal.get("platforms", [])
                        if platform.get("name")
                    ],
                    "expires_at": (
                        datetime.fromisoformat(expiry).strftime("%d %B %Y at %H:%M")
                        if expiry
                        else None
                    ),
                    "url": deal.get("url"),
                }
            )

        return deals_for_ai
