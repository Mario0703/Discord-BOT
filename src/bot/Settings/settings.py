import os
import warnings
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from bot.errors import ConfigurationError
from bot.openai_models import MODEL_REASONING_LEVELS


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

    def __post_init__(self) -> None:
        numeric_limits = {
            "summary_max_days": self.summary_max_days,
            "summary_max_messages": self.summary_max_messages,
            "summary_max_characters": self.summary_max_characters,
            "upload_max_bytes": self.upload_max_bytes,
            "tts_max_characters": self.tts_max_characters,
            "max_tool_calls": self.max_tool_calls,
        }
        for name, value in numeric_limits.items():
            if value <= 0:
                raise ConfigurationError(f"{name} must be greater than zero.")

        if self.openai_model not in MODEL_REASONING_LEVELS:
            raise ConfigurationError(
                f"Unsupported OpenAI model: {self.openai_model}."
            )

        supported_levels = MODEL_REASONING_LEVELS[self.openai_model]
        if self.openai_reasoning_level not in supported_levels:
            raise ConfigurationError(
                f"Reasoning level {self.openai_reasoning_level!r} is not "
                f"supported by {self.openai_model!r}."
            )


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


def _check_api_keys_settings(settings: Settings) -> bool:
    """Warn about missing optional provider keys without stopping startup."""
    optional_keys = {
        "ELEVENLABS_API_KEY": settings.elevenlabs_api_key,
        "ITAD_API_KEY": settings.itad_api_key,
        "OPENWEATHER_API_KEY": settings.openweather_api_key,
    }
    missing_keys = [name for name, value in optional_keys.items() if not value]
    if not missing_keys:
        return True

    warnings.warn(
        f"{len(missing_keys)} optional API key(s) are missing: "
        f"{', '.join(missing_keys)}. The bot will start, but the related "
        "features will be unavailable.",
        RuntimeWarning,
        stacklevel=2,
    )
    return False


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
