from __future__ import annotations

from typing import cast

from openai import BadRequestError, NotFoundError
from openai.types.responses import Response
from openai.types.shared import ReasoningEffort
from openai.types.shared_params import Reasoning

from bot.errors import InvalidInput, ToolCallLimitError
from bot.settings.settings import Settings
from bot.storage.token_usage import TokenUsage
from bot.storage.user_conversations import UserConversations

from .model_preference_service import ModelPreferenceService
from .openai_gateway import OpenAIGateway
from .provider_errors import openai_errors
from .tool_dispatcher import ToolDispatcher


class AssistantService:
    """Coordinate conversations, preferences, tools, and OpenAI responses."""

    def __init__(
        self,
        open_ai_gateway: OpenAIGateway,
        model_preference_service: ModelPreferenceService,
        tool_dispatcher: ToolDispatcher,
        conversations: UserConversations,
        token_usage: TokenUsage,
        settings: Settings,
    ) -> None:
        self.gateway = open_ai_gateway
        self.model_preferences = model_preference_service
        self.tool_dispatcher = tool_dispatcher
        self.conversations = conversations
        self.token_usage = token_usage
        self.settings = settings
        self.input_token_count = 0
        self.output_token_count = 0

    async def generate_response(
        self,
        prompt: str,
        user_id: str | int,
        workflow: str = "assistant",
    ) -> str:
        """Return the final text for a stateful user conversation."""
        response = await self.create_response_conversations(
            prompt,
            user_id,
            workflow=workflow,
        )
        return response.output_text

    async def create_response_conversations(
        self,
        prompt: str,
        user_id: str | int,
        workflow: str = "assistant",
    ) -> Response:
        """Create a response in a workflow-specific user conversation."""
        if not prompt.strip():
            raise InvalidInput("The prompt must not be empty.")
        async with openai_errors():
            conversation_id = self.conversations.get_conversation(user_id, workflow)
            if conversation_id is None:
                conversation_id = await self.gateway.create_conversation()
                self.conversations.update_conversation(
                    user_id,
                    conversation_id,
                    workflow,
                )

            model_id, reasoning_level = self.model_preferences.resolve(user_id)
            try:
                response = await self._create_initial_response(
                    prompt=prompt,
                    model_id=model_id,
                    reasoning_level=reasoning_level,
                    conversation_id=conversation_id,
                )
            except (NotFoundError, BadRequestError) as error:
                if isinstance(error, BadRequestError) and (
                    "No tool output found for function call" not in error.message
                ):
                    raise

                conversation_id = await self.gateway.create_conversation()
                self.conversations.update_conversation(
                    user_id,
                    conversation_id,
                    workflow,
                )
                response = await self._create_initial_response(
                    prompt=prompt,
                    model_id=model_id,
                    reasoning_level=reasoning_level,
                    conversation_id=conversation_id,
                )
            return await self._complete_response(
                prompt=prompt,
                model_id=model_id,
                reasoning_level=reasoning_level,
                user_id=user_id,
                conversation_id=conversation_id,
                initial_response=response,
            )

    async def get_stateless_response(
        self,
        prompt: str,
        user_id: str | int,
        allow_tools: bool = False,
    ) -> str:
        """Return text without reading or writing conversation history."""
        model_id, reasoning_level = self.model_preferences.resolve(user_id)
        response = await self.create_response_without_conversation(
            prompt,
            model_id,
            reasoning_level,
            user_id=user_id,
            allow_tools=allow_tools,
        )
        return response.output_text

    async def create_response_without_conversation(
        self,
        prompt: str,
        model_id: str,
        reasoning_level: str | None,
        user_id: str | int | None = None,
        allow_tools: bool = True,
    ) -> Response:
        """Create a stateless response, optionally attributing token usage."""
        if not prompt.strip():
            raise InvalidInput("The prompt must not be empty.")
        async with openai_errors():
            return await self._complete_response(
                prompt=prompt,
                model_id=model_id,
                reasoning_level=reasoning_level,
                user_id=user_id,
                conversation_id=None,
                allow_tools=allow_tools,
            )

    async def clear_conversation(
        self,
        user_id: str | int,
        workflow: str = "assistant",
    ) -> bool:
        conversation_id = self.conversations.get_conversation(user_id, workflow)
        if conversation_id is None:
            return False

        await self.gateway.remove_conversation(conversation_id)
        self.conversations.remove_conversation(user_id, workflow)
        return True

    async def _complete_response(
        self,
        prompt: str,
        model_id: str,
        reasoning_level: str | None,
        user_id: str | int | None,
        conversation_id: str | None,
        allow_tools: bool = True,
        initial_response: Response | None = None,
    ) -> Response:
        reasoning: Reasoning | None = (
            {"effort": cast(ReasoningEffort, reasoning_level)}
            if reasoning_level is not None
            else None
        )
        tool_definitions = (
            self.tool_dispatcher.get_tool_definitions() if allow_tools else []
        )
        response = initial_response
        if response is None:
            response = await self.gateway.create_response(
                model_id=model_id,
                input=prompt,
                conversation_id=conversation_id,
                reasoning=reasoning,
                tool_definitions=tool_definitions,
            )
        self._record_usage(user_id, response)

        tool_call_count = 0
        while True:
            requested_calls = sum(
                item.type == "function_call" for item in response.output
            )
            if tool_call_count + requested_calls > self.settings.max_tool_calls:
                raise ToolCallLimitError(
                    "This request exceeded the maximum of "
                    f"{self.settings.max_tool_calls} tool calls. "
                    "Please try a simpler request."
                )

            tool_outputs = await self.tool_dispatcher.execute_tool_calls(response)
            if not tool_outputs:
                return response

            tool_call_count += len(tool_outputs)
            previous_response_id = None if conversation_id else response.id
            response = await self.gateway.create_response(
                model_id=model_id,
                input=tool_outputs,
                conversation_id=conversation_id,
                reasoning=reasoning,
                tool_definitions=tool_definitions,
                previous_response_id=previous_response_id,
            )
            self._record_usage(user_id, response)

    async def _create_initial_response(
        self,
        prompt: str,
        model_id: str,
        reasoning_level: str | None,
        conversation_id: str,
    ) -> Response:
        reasoning: Reasoning | None = (
            {"effort": cast(ReasoningEffort, reasoning_level)}
            if reasoning_level is not None
            else None
        )
        return await self.gateway.create_response(
            model_id=model_id,
            input=prompt,
            conversation_id=conversation_id,
            reasoning=reasoning,
            tool_definitions=self.tool_dispatcher.get_tool_definitions(),
        )

    def _record_usage(self, user_id: str | int | None, response: Response) -> None:
        if user_id is None or response.usage is None:
            return
        self.input_token_count += response.usage.input_tokens
        self.output_token_count += response.usage.output_tokens
        self.token_usage.record(
            user_id,
            response.usage.input_tokens,
            response.usage.output_tokens,
        )
