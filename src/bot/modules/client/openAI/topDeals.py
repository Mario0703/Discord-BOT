import asyncio
import json
from datetime import datetime
from typing import Any

from openai import OpenAI

from bot.tools.gamesDeal import GamesDealTool


class TopDealsService:
    """Fetch and present the three strongest current Steam deals."""

    def __init__(self, client: OpenAI, deals_tool: GamesDealTool):
        self.client = client
        self.deals_tool = deals_tool

    def get_top_steam_deals(
        self,
        country: str = "DK",
        minimum_discount: int = 80,
    ) -> str:
        raw_deals = asyncio.run(
            self.deals_tool.execute(
                country=country,
                shop=61,
                discount_min=minimum_discount,
                discount_max=100,
            )
        )

        response = self.client.responses.create(
            model="gpt-5.6-luna",
            input=self._ranking_prompt(self._normalise_deals(raw_deals)),
        )
        return response.output_text

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

    @staticmethod
    def _ranking_prompt(deals: list[dict[str, Any]]) -> str:
        instructions = """
        Find the three hottest Steam deals in the supplied JSON data and rank them from
        hottest to least hot. Prefer a higher discount percentage; use a lower current
        price only as a tie-breaker.

        For each deal, return: title, current price, regular price, discount,
        platforms, store, expiry, and URL. If a supplied field is missing, write
        "Unknown". Do not infer historical lows, genres, gameplay, multiplayer
        support, or whether an item is a full game, DLC, or a package.

        Only report information present in the supplied data.

        Deal data:
        """
        return instructions + json.dumps(deals, indent=2)
