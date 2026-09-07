import logging
from collections.abc import Iterable, Iterator
from pathlib import Path

import httpx
from elevenlabs.client import ElevenLabs
from elevenlabs.core.api_error import ApiError

from bot.errors import (
    ExternalServiceUnavailable,
    InvalidInput,
    MissingConfigurationError,
    OptionalFeatureUnavailableError,
)
from bot.settings.settings import Settings


class ElevenLabsClient:
    """Convert text to speech using ElevenLabs."""

    def __init__(
        self,
        voice_id: str = "JBFqnCBsd6RMkjVDRZzb",
        model_id: str = "eleven_multilingual_v2",
        settings: Settings | None = None,
    ) -> None:
        if settings is None:
            raise MissingConfigurationError("Settings are required.")

        self.settings = settings
        self.voice_id = voice_id
        self.model_id = model_id
        self.speech_dir = settings.data_dir / "speech"
        self.client = (
            ElevenLabs(api_key=settings.elevenlabs_api_key)
            if settings.elevenlabs_api_key
            else None
        )

    def convert_text_to_speech(self, text: str) -> Iterator[bytes]:
        """Return generated audio chunks for the supplied text."""
        if self.client is None:
            raise OptionalFeatureUnavailableError(
                "ElevenLabs speech is unavailable because ELEVENLABS_API_KEY "
                "is not configured."
            )
        if not text or not text.strip():
            raise InvalidInput("Text to convert cannot be empty")

        if len(text) > self.settings.tts_max_characters:
            raise InvalidInput(
                "The text cannot exceed "
                f"{self.settings.tts_max_characters:,} characters."
            )
        return self._audio_chunks(text)

    def _audio_chunks(self, text: str) -> Iterator[bytes]:
        assert self.client is not None
        try:
            yield from self.client.text_to_speech.convert(
                voice_id=self.voice_id,
                model_id=self.model_id,
                output_format="mp3_44100_128",
                text=text,
            )
        except (ApiError, httpx.HTTPError) as error:
            logging.getLogger(__name__).warning(
                "ElevenLabs request failed (%s)", type(error).__name__
            )
            raise ExternalServiceUnavailable(
                "Speech generation is temporarily unavailable."
            ) from error

    def save_audio(
        self,
        audio: Iterable[bytes],
        output_path: str | Path = "speech.mp3",
    ) -> Path:
        """Save generated audio chunks to an MP3 file."""
        path = Path(output_path)
        if not path.is_absolute():
            path = self.speech_dir / path
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("wb") as output_file:
            for chunk in audio:
                if chunk:
                    output_file.write(chunk)

        return path
