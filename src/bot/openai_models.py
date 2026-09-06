"""OpenAI models and reasoning levels supported by the bot."""

from collections.abc import Mapping
from types import MappingProxyType

MODEL_REASONING_LEVELS: Mapping[str, tuple[str, ...]] = {
        "gpt-5.6-luna": ("none", "low", "medium", "high", "xhigh", "max"),
        "gpt-5.6-terra": ("none", "low", "medium", "high", "xhigh", "max"),
        "gpt-5.6-sol": ("none", "low", "medium", "high", "xhigh", "max"),
        "gpt-5": ("minimal", "low", "medium", "high"),
 }

