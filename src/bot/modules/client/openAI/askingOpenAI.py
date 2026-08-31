import asyncio
import json
import os
from datetime import datetime
from collections.abc import Iterable
from typing import Any

from openai import OpenAI
from ..API.isThereSuchDeal import Deals
from bot.tools.tool import tool as Tool

class AskOpenAI:

    def __init__(self, tools: Iterable[Tool], client: OpenAI | None = None):
        self.client = (
            client if client is not None else OpenAI(api_key=os.getenv("API_KEY"))
        )
        registered_tools = tuple(tools)
        self._tools_by_name = {tool.name: tool for tool in registered_tools}

        if len(self._tools_by_name) != len(registered_tools):
            raise ValueError("Every registered tool must have a unique name")

        self._tool_definitions: list[dict[str, Any]] = [
            tool.definition() for tool in registered_tools
        ]

    def ask_openai(self, prompt: str) -> str:
        response = self.client.responses.create(
            model="gpt-5.6-luna",
            input=prompt,
            tools=self._tool_definitions,
        )

        while True:
            tool_outputs = []

            for item in response.output:
                if item.type != "function_call":
                    continue

                tool = self._tools_by_name.get(item.name)

                if tool is None:
                    tool_outputs.append(
                        {
                            "type": "function_call_output",
                            "call_id": item.call_id,
                            "output": json.dumps({"error": f"Unknown tool: {item.name}"}),
                        }
                    )
                    continue

                try:
                    arguments = json.loads(item.arguments)
                    result = asyncio.run(tool.execute(**arguments))
                except Exception as error:
                    result = {"error": str(error)}

                tool_outputs.append(
                    {
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": json.dumps(result),
                    }
                )

            # No tool requests: the model produced its final answer.
            if not tool_outputs:
                return response.output_text

            # Send results back for the exact preceding response.
            response = self.client.responses.create(
                model="gpt-5.6-luna",
                previous_response_id=response.id,
                input=tool_outputs,
                tools=self._tool_definitions,
            )

    def ask_openai_about_good_deals(self):
        deals_client = Deals(country="DK", shop="61", discount_range=(80, 100))
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
