from collections.abc import Iterable
from pathlib import Path

from elevenlabs.client import ElevenLabs
from elevenlabs.play import play

from ..API.api_client import ApiClient


class ElevenLabsClient(ApiClient):
    """Convert text to speech using ElevenLabs."""

    API_KEY_ENV_VAR = "ELEVENLABS_API_KEY"

    def __init__(
        self,
        voice_id: str = "JBFqnCBsd6RMkjVDRZzb",
        model_id: str = "eleven_multilingual_v2",
    ):
        self.voice_id = voice_id
        self.model_id = model_id
        self.client = ElevenLabs(api_key=self.get_api_key())

    def convert_text_to_speech(self, text: str) -> Iterable[bytes]:
        """Return generated audio chunks for the supplied text."""
        if not text or not text.strip():
            raise ValueError("Text to convert cannot be empty")

        return self.client.text_to_speech.convert(
            voice_id=self.voice_id,
            model_id=self.model_id,
            output_format="mp3_44100_128",
            text=text,
        )

    def save_audio(self, audio: Iterable[bytes], output_path: str | Path) -> Path:
        """Save generated audio chunks to an MP3 file."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("wb") as output_file:
            for chunk in audio:
                if chunk:
                    output_file.write(chunk)

        return path

    def play_audio(self, audio: Iterable[bytes]) -> None:
        """Play generated audio locally; requires a supported player such as MPV."""
        play(audio)
