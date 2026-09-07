from __future__ import annotations

from collections.abc import Sequence
from typing import BinaryIO

from openai import AsyncOpenAI
from openai.pagination import AsyncPage
from openai.types import Model
from openai.types.responses import Response, ResponseInputParam, ToolParam
from openai.types.responses.response_create_params import (
    ResponseCreateParamsNonStreaming,
)
from openai.types.shared_params import Reasoning

from bot.errors import MissingConfigurationError
from bot.settings.settings import Settings

from .provider_errors import openai_errors


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
        input: str | ResponseInputParam,
        conversation_id: str | None = None,
        reasoning: Reasoning | None = None,
        tool_definitions: Sequence[ToolParam] | None = None,
        previous_response_id: str | None = None,
    ) -> Response:
        async with openai_errors(allow_conversation_recovery=True):
            request: ResponseCreateParamsNonStreaming = dict(
                model=model_id,
                conversation=conversation_id,
                input=input,
                reasoning=reasoning,
                tools=list(tool_definitions or []),
            )
            if previous_response_id is not None:
                request["previous_response_id"] = previous_response_id
            return await self.client.responses.create(**request)

    async def create_conversation(self) -> str:
        async with openai_errors():
            conversation = await self.client.conversations.create()
            return conversation.id

    async def remove_conversation(self, conversation_id: str) -> None:
        async with openai_errors():
            await self.client.conversations.delete(conversation_id)

    async def get_models(self) -> AsyncPage[Model]:
        async with openai_errors():
            return await self.client.models.list()

    async def create_transcription(
        self,
        audio_file: BinaryIO,
        model_id: str = "gpt-4o-transcribe",
    ) -> str:
        async with openai_errors():
            transcript = await self.client.audio.transcriptions.create(
                model=model_id,
                file=audio_file,
            )
            return transcript.text
