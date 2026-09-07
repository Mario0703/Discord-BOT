from __future__ import annotations

from typing import Any

from openai import AsyncOpenAI


class OpenAIGateway:
    """Provide direct access to the OpenAI SDK operations used by the bot."""

    def __init__(self, client: AsyncOpenAI) -> None:
        self.client = client

    async def create_response(
        self,
        model_id: str,
        input: str | list[dict[str, Any]],
        conversation_id: str | None = None,
        reasoning: dict[str, Any] | None = None,
        tool_definitions: list[dict[str, Any]] | None = None,
    ) -> Any:
        return await self.client.responses.create(
            model=model_id,
            conversation=conversation_id,
            input=input,
            reasoning=reasoning,
            tools=tool_definitions or [],
        )

    async def create_conversation(self) -> str:
        conversation = await self.client.conversations.create()
        return conversation.id

    async def remove_conversation(self, conversation_id: str) -> None:
        await self.client.conversations.delete(conversation_id)

    async def get_models(self) -> Any:
        return await self.client.models.list()


OpenAiGateway = OpenAIGateway
