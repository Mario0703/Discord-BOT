from __future__ import annotations

from typing import Any, BinaryIO

from openai import AsyncOpenAI

from bot.errors import MissingConfigurationError
from bot.Settings.settings import Settings


class OpenAIGateway:
    """Provide direct access to the OpenAI SDK operations used by the bot."""

    def __init__(
        self,
        client: AsyncOpenAI | None = None,
        settings: Settings | None = None,
    ) -> None:
        if client is None:
            if settings is None:
                raise MissingConfigurationError("Settings are required.")
            if not settings.openai_api_key:
                raise MissingConfigurationError("OpenAI API key is required.")
            client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.client = client

    async def create_response(
        self,
        model_id: str,
        input: str | list[dict[str, Any]],
        conversation_id: str | None = None,
        reasoning: dict[str, Any] | None = None,
        tool_definitions: list[dict[str, Any]] | None = None,
        previous_response_id: str | None = None,
    ) -> Any:
        request: dict[str, Any] = dict(
            model=model_id,
            conversation=conversation_id,
            input=input,
            reasoning=reasoning,
            tools=tool_definitions or [],
        )
        if previous_response_id is not None:
            request["previous_response_id"] = previous_response_id
        return await self.client.responses.create(**request)

    async def create_conversation(self) -> str:
        conversation = await self.client.conversations.create()
        return conversation.id

    async def remove_conversation(self, conversation_id: str) -> None:
        await self.client.conversations.delete(conversation_id)

    async def get_models(self) -> Any:
        return await self.client.models.list()

    async def create_transcription(
        self,
        audio_file: BinaryIO,
        model_id: str = "gpt-4o-transcribe",
    ) -> str:
        transcript = await self.client.audio.transcriptions.create(
            model=model_id,
            file=audio_file,
        )
        return transcript.text
