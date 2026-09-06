import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    discord_token: str = field(repr=False)
    guild_ids: tuple[int, ...] = ()
    openai_api_key: str = field(repr=False, default="")
    openai_model: str = "gpt-5.6-luna"
    openai_reasoning_level: str = "medium"
    elevenlabs_api_key: str | None = field(default=None, repr=False)
    itad_api_key: str | None = field(default=None, repr=False)
    openweather_api_key: str | None = field(default=None, repr=False)
    data_dir: Path = Path("data")

    summary_max_days: int = 7
    summary_max_messages: int = 1_000
    summary_max_characters: int = 50_000
    upload_max_bytes: int = 10 * 1024 * 1024
    tts_max_characters: int = 5_000
    max_tool_calls: int = 5


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            "Copy .env.example to .env and fill in the required values."
        )
    return value


def _guild_ids() -> tuple[int, ...]:
    raw_value = _required("GUILD_IDS")
    try:
        guild_ids = tuple(int(value.strip()) for value in raw_value.split(","))
    except ValueError as error:
        raise RuntimeError(
            "GUILD_IDS must contain comma-separated Discord server IDs."
        ) from error

    if not guild_ids:
        raise RuntimeError("GUILD_IDS must contain at least one server ID.")
    return guild_ids


def load_settings() -> Settings:
    load_dotenv()

    return Settings(
        discord_token=_required("TOKEN"),
        guild_ids=_guild_ids(),
        openai_api_key=_required("OPENAI_API_KEY"),
        elevenlabs_api_key=os.getenv("ELEVENLABS_API_KEY") or None,
        itad_api_key=os.getenv("ITAD_API_KEY") or None,
        openweather_api_key=os.getenv("OPENWEATHER_API_KEY") or None,
    )
