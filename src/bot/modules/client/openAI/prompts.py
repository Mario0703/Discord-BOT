"""Prompt builders used by the OpenAI services.

Keeping prompts here makes them easy to review and change without mixing
prompt wording with API and tool-calling code.
"""

import json
from typing import Any


def assistant_prompt(prompt: str) -> str:
    """Return the prompt used for a normal assistant question."""
    return prompt


def ranking_prompt(deals: list[dict[str, Any]]) -> str:
    """Build the prompt used to rank Steam deals."""
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
