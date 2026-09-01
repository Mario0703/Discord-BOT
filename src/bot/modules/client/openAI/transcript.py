from openai import AsyncOpenAI


class Transcript:
    def __init__(self, client: AsyncOpenAI | None = None):
        self.client = client or AsyncOpenAI()

    async def create_transcript(self, audio_file_path: str) -> str:
        with open(audio_file_path, "rb") as audio_file:
            transcript = await self.client.audio.transcriptions.create(
                model="gpt-4o-transcribe",
                file=audio_file,
            )
        return transcript.text
