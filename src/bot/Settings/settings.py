from dataclasses import dataclass

from anyio import Path
from attrs import field
import os
from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    discord_token: str
    guild_ids: tuple[int, ...]

    openai_api_key: str
    openai_model: str
    openai_reasoning_level: str

    elevenlabs_api_key: str | None
    itad_api_key: str | None
    openweather_api_key: str | None

    data_dir: Path

    summary_max_days: int
    summary_max_messages: int
    summary_max_characters: int

    upload_max_bytes: int
    tts_max_characters: int

    max_tool_calls: int

    openai_api_key: str = field(repr=False)
    elevenlabs_api_key: str | None = field(default=None, repr=False)
    itad_api_key: str | None = field(default=None, repr=False)
    openweather_api_key: str | None = field(default=None, repr=False)

    discord_token: str = ""
    guild_ids: tuple[int, ...] = ()
    openai_model: str = "gpt-5.6-luna"
    openai_reasoning_level: str = "medium"
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
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def load_settings() -> Settings:
    load_dotenv()

    guild_ids = tuple(
        int(guild_id.strip()) for guild_id in _required("GUILD_IDS").split(",")
    )

    return Settings(
        discord_token=_required("TOKEN"),
        guild_ids=guild_ids,
        openai_api_key=_required("OPENAI_API_KEY"),
        elevenlabs_api_key=os.getenv("ELEVENLABS_API_KEY"),
        itad_api_key=os.getenv("ITAD_API_KEY"),
        openweather_api_key=os.getenv("OPENWEATHER_API_KEY"),
    )
