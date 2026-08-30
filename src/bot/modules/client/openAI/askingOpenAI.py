import json
import os

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
                    "type": item.get("type"),
                    "shop": deal.get("shop", {}).get("name"),
                    "current_price": deal.get("price", {}).get("amount"),
                    "regular_price": deal.get("regular", {}).get("amount"),
                    "currency": deal.get("price", {}).get("currency"),
                    "discount_percent": deal.get("cut"),
                    "store_low": (
                        deal["storeLow"]["amount"] if deal.get("storeLow") else None
                    ),
                    "history_low": (
                        deal["historyLow"]["amount"] if deal.get("historyLow") else None
                    ),
                    "history_low_3m": (
                        deal["historyLow_3m"]["amount"]
                        if deal.get("historyLow_3m")
                        else None
                    ),
                    "deal_flag": deal.get("flag"),
                    "platforms": [
                        platform["name"] for platform in deal.get("platforms", [])
                    ],
                    "expiry": deal.get("expiry"),
                    "url": deal.get("url"),
                }
            )

        prompt = """
    Find the hottest Steam game deals from the JSON data below.

    Prioritize:
    - discount_percent >= 80
    - current_price at or below a historical low
    - deals that have not expired
    - full games over DLC and packages
    - deal_flag "H" and free games

    For each selected deal, explain:
    - what the game is about
    - whether it is fun with friends
    - who it is suitable for
    - why the user might enjoy it
    - why the deal is attractive

    Return:
    title, type, current price, regular price, discount,
    platforms, expiry, URL, and a short recommendation.

    Do not recommend expired deals. If information is missing, write "Unknown".
    Do not invent specific game details that are not present in the data.

    Deal data:
    """

        response = self.client.responses.create(
            model="gpt-5.6-luna",
            input=prompt + json.dumps(deals_for_ai, indent=2),
        )

        return response.output_text
