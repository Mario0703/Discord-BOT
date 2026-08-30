import json
import os
from datetime import datetime

from openai import OpenAI
from ..API.isThereSuchDeal import Deals


class AskOpenAI:

    def __init__(self, client=None):
        self.client = (
            client if client is not None else OpenAI(api_key=os.getenv("API_KEY"))
        )

    def ask_openai(self, prompt: str) -> str:
        response = self.client.responses.create(
            model="gpt-5.6-luna",
            input=prompt,
        )
        return response.output_text

    def ask_openai_about_good_deals(self):
        deals_client = Deals()
        result = deals_client.get_steam_deals(os.environ["ITAD_API_KEY"])

        deals_for_ai = []

        for item in result.get("list", []):
            deal = item.get("deal", {})

            deals_for_ai.append(
                {
                    "title": item.get("title"),
                    "store": deal.get("shop", {}).get("name"),
                    "current_price": deal.get("price", {}).get("amount"),
                    "regular_price": deal.get("regular", {}).get("amount"),
                    "currency": deal.get("price", {}).get("currency"),
                    "discount_percent": deal.get("cut"),
                    "platforms": [
                        platform["name"] for platform in deal.get("platforms", [])
                    ],
                    "expires_at": (
                        datetime.fromisoformat(deal["expiry"]).strftime(
                            "%d %B %Y at %H:%M"
                        )
                        if deal.get("expiry")
                        else None
                    ),
                    "url": deal.get("url"),
                }
            )

        prompt = """
    Find the hottest Steam game deals from the JSON data below.

    Select no more than 3 deals. Rank them from hottest to least hot.

    Prioritize:
    - discount_percent >= 80
    - current_price at or below a historical low
    - deals that have not expired
    - full games over DLC and packages
    - free games and unusually large discounts

    Return:
    title, current price, regular price, discount, platforms,
    store, expires_at (when the deal is no longer valid),
    and URL.

    Do not include expired deals. If a deal field is missing, write "Unknown".
    Only report information present in the supplied data; do not infer game
    descriptions, genres, gameplay, or multiplayer support.

    Deal data:
    """

        response = self.client.responses.create(
            model="gpt-5.6-luna",
            input=prompt + json.dumps(deals_for_ai, indent=2),
        )

        return response.output_text
