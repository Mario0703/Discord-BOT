import json
from collections.abc import Iterable

import discord
from openai import AsyncOpenAI, NotFoundError

from bot.tools.tool import tool as Tool

from ....model_selections import (
    MODEL_REASONING_LEVELS,
    ModelSelectionStore,
    resolve_model_settings,
)
from ....token_usage import TokenUsage
from ....user import User
from ....user_conversations import UserConversations
from ..API.api_client import ApiClient
from .prompts import assistant_prompt

class OpenAiCLientImpl(ApiClient):
    API_KEY_ENV_VAR = "API_KEY"

    def __init__(
        self,
        tools: Iterable[Tool] = (),
        client: AsyncOpenAI | None = None,
        user_conversations: UserConversations | None = None,
        token_usage: TokenUsage | None = None,
        model_selection_store: ModelSelectionStore | None = None,
    ):
        self._tools_by_name = {}
        self._tool_definitions = []
        self.user_conversations = user_conversations or UserConversations()
        self.token_usage = token_usage or TokenUsage()
        self.model_selection_store = model_selection_store or ModelSelectionStore()
        self.input_token_count = 0
        self.output_token_count = 0
        registered_tools = tuple(tools)

        if client is not None:
            self.client = client
        else:
            self.client = AsyncOpenAI(api_key=self.get_api_key())

        for tool in registered_tools:
            self._tools_by_name[tool.name] = tool

        if len(self._tools_by_name) != len(registered_tools):
            raise ValueError("Every registered tool must have a unique name")

        for tool in registered_tools:
            self._tool_definitions.append(tool.definition())

    async def generate_repsone_from_openAI(
        self, prompt: str, ctx: discord.ApplicationContext
    ) -> str:
        user_id = User(ctx).get_discord_id()
        conversation_id = self.user_conversations.get_conversation(user_id)
        model_id, reasoning_level = self._get_user_model_settings(user_id)

        if conversation_id is None:
            conversation = await self.client.conversations.create()
            conversation_id = conversation.id
            self.user_conversations.update_conversation(user_id, conversation_id)

        request = {
            "model": model_id,
            "input": assistant_prompt(prompt),
            "conversation": conversation_id,
        }
        if reasoning_level is not None:
            request["reasoning"] = {"effort": reasoning_level}
        if self._tool_definitions:
            request["tools"] = self._tool_definitions
        try:
            response = await self.client.responses.create(**request)
        except NotFoundError:
            # Conversations are stored remotely. A local ID can become stale if
            # it was deleted in OpenAI, created under another project, or has
            # otherwise become unavailable.
            self.user_conversations.remove_conversation(user_id)
            conversation = await self.client.conversations.create()
            conversation_id = conversation.id
            self.user_conversations.update_conversation(user_id, conversation_id)
            request["conversation"] = conversation_id
            response = await self.client.responses.create(**request)
        self._record_usage(user_id, response)

        while True:
            tool_outputs = []
            for item in response.output:
                if item.type != "function_call":
                    continue

                tool = self._tools_by_name.get(item.name)

                if tool is None:
                    tool_outputs.append(
                        {
                            "type": "function_call_output",
                            "call_id": item.call_id,
                            "output": json.dumps(
                                {"error": f"Unknown tool: {item.name}"}
                            ),
                        }
                    )
                    continue

                try:
                    arguments = json.loads(item.arguments)
                    result = await tool.execute(**arguments)
                except Exception as error:
                    result = {"error": str(error)}

                tool_outputs.append(
                    {
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": json.dumps(result),
                    }
                )
            # No tool requests: the model produced its final answer.
            if not tool_outputs:
                return response.output_text

            # Send results back for the exact preceding response.
            follow_up_request = {
                "model": model_id,
                "previous_response_id": response.id,
                "input": tool_outputs,
                "tools": self._tool_definitions,
            }
            if reasoning_level is not None:
                follow_up_request["reasoning"] = {"effort": reasoning_level}

            response = await self.client.responses.create(
                **follow_up_request
            )

            self._record_usage(user_id, response)

    def _get_user_model_settings(self, user_id: str) -> tuple[str, str | None]:
        """Use a saved profile when valid, otherwise use the bot defaults."""
        selection = self.model_selection_store.get_selection(user_id)
        return resolve_model_settings(selection)

    def _record_usage(self, user_id: str, response) -> None:
        usage = response.usage
        if usage is None:
            return

        self.input_token_count += usage.input_tokens
        self.output_token_count += usage.output_tokens
        self.token_usage.record(
            user_id,
            usage.input_tokens,
            usage.output_tokens,
        )

    def get_token_report(self) -> dict[str, dict[str, int]]:
        return self.token_usage.report()

    def get_token_usage(self) -> tuple[int, int]:
        """Get the total input and output token usage."""
        return self.input_token_count, self.output_token_count

    async def clear_conversation(self, ctx: discord.ApplicationContext) -> bool:
        """Delete the user's OpenAI conversation and local mapping."""
        user_id = User(ctx).get_discord_id()
        conversation_id = self.user_conversations.get_conversation(user_id)

        if conversation_id is None:
            return False

        await self.client.conversations.delete(conversation_id)
        self.user_conversations.remove_conversation(user_id)
        return True

    async def get_model_list(self) -> list[str]:
        model_id = []
        response = self.client.models.list()
        async for model in response:
            model_id.append(model.id)
        return model_id

    async def get_model_info(self) -> dict[str, list[str]]:
        """Return configured models available to this API key and their reasoning levels."""
        available_model_ids = set(await self.get_model_list())
        models_dict = {}

        for model_id, reasoning_levels in MODEL_REASONING_LEVELS.items():
            if model_id in available_model_ids:
                models_dict[model_id] = reasoning_levels

        return models_dict

    async def set_user_model(
        self,
        ctx: discord.ApplicationContext,
        model_id: str,
        reasoning_level: str,
    ) -> bool:
        """Validate and save a Discord user's model preference."""
        supported_levels = MODEL_REASONING_LEVELS.get(model_id)

        if supported_levels is None or reasoning_level not in supported_levels:
            return False

        user_id = User(ctx).get_discord_id()
        self.model_selection_store.set_selection(
            user_id,
            model_id,
            reasoning_level,
        )
        return True

    def get_user_model(self, ctx: discord.ApplicationContext):
        """Return the saved model preference for the Discord user, if one exists."""
        user_id = User(ctx).get_discord_id()
        return self.model_selection_store.get_selection(user_id)
