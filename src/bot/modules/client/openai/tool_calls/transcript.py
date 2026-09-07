from ..orchestration import OpenAIGateway


class Transcript:
    "Creates a transcript from an audio file using the OpenAI service."

    def __init__(self, gateway: OpenAIGateway) -> None:
        self.gateway = gateway

    async def create_transcript(self, audio_file_path: str) -> str:
        with open(audio_file_path, "rb") as audio_file:
            return await self.gateway.create_transcription(audio_file)
