from ..openai_client_impl import OpenAiCLientImpl


class Transcript:
    "Creates a transcript from an audio file using the OpenAI service."

    def __init__(self, openai_service: OpenAiCLientImpl):
        self.openai_service = openai_service

    async def create_transcript(self, audio_file_path: str) -> str:
        with open(audio_file_path, "rb") as audio_file:
            transcript = await self.openai_service.client.audio.transcriptions.create(
                model="gpt-4o-transcribe",
                file=audio_file,
            )
        return transcript.text
