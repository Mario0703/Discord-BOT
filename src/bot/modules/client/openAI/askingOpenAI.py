import json
from typing import List

import discord
from openai import AsyncOpenAI, BadRequestError, NotFoundError

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
        tools: List[Tool] | None = None,
        client: AsyncOpenAI | None = None,
        user_conversations: UserConversations | None = None,
        token_usage: TokenUsage | None = None,
        model_selection_store: ModelSelectionStore | None = None,
    ):
        self.user_conversations = user_conversations or UserConversations()
        self.token_usage = token_usage or TokenUsage()
        self.model_selection_store = model_selection_store or ModelSelectionStore()
        self.input_token_count = 0
        self.output_token_count = 0
        self.tools = tools or []
        if client is not None:
            self.client = client
        else:
            self.client = AsyncOpenAI(api_key=self.get_api_key())


    async def generate_repsone_from_openAI(
        self, prompt: str, ctx: discord.ApplicationContext
    ) -> str:
        user_id = User(ctx).get_discord_id()
        conversation_id = self.user_conversations.get_conversation(user_id)
        model_id, reasoning_level = self._get_user_model_settings(user_id)

        if conversation_id is None:
            conversation_id = await self._create_conversation(user_id)
        
        tool_definitions = self._get_tool_definitions()
        reasoning = None
        if reasoning_level is not None:
            reasoning = {"effort": reasoning_level}

        response, conversation_id = await self._create_initial_response(
            user_id, prompt, conversation_id, model_id, tool_definitions, reasoning
        )
        self._record_usage(user_id, response)

        while True:
            tool_outputs = await self._execute_tool_calls(response)
            if not tool_outputs:
                return response.output_text

            response = await self.client.responses.create(
                model=model_id,
                conversation=conversation_id,
                input=tool_outputs,
                reasoning=reasoning,
                tools=tool_definitions,
            )
            self._record_usage(user_id, response)

    def _get_tool_definitions(self) -> list[dict]:
        tool_definitions = []
        for tool in self.tools:
            tool_definitions.append(tool.definition())
        return tool_definitions

    async def _create_initial_response(
        self, user_id, prompt, conversation_id, model_id, tool_definitions, reasoning
    ):
        try:
            response = await self.client.responses.create(
                model=model_id,
                input=assistant_prompt(prompt),
                conversation=conversation_id,
                tools=tool_definitions,
                reasoning=reasoning,
            )
        except (NotFoundError, BadRequestError) as error:
            if isinstance(error, BadRequestError):
                if "No tool output found for function call" not in error.message:
                    raise
            conversation_id = await self._create_conversation(user_id)
            response = await self.client.responses.create(
                model=model_id,
                input=assistant_prompt(prompt),
                conversation=conversation_id,
                tools=tool_definitions,
                reasoning=reasoning,
            )
        return response, conversation_id

    def _find_tool(self, name: str) -> Tool | None:
        for available_tool in self.tools:
            if available_tool.name == name:
                return available_tool
        return None

    async def _execute_tool_calls(self, response) -> list[dict]:
        tool_outputs = []
        for output_item in response.output:
            if output_item.type != "function_call":
                continue

            tool = self._find_tool(output_item.name)
            if tool is None:
                result = {"error": f"Unknown tool: {output_item.name}"}
            else:
                try:
                    arguments = json.loads(output_item.arguments)
                    result = await tool.execute(**arguments)
                except Exception as error:
                    result = {"error": str(error)}

            tool_outputs.append(
                {
                    "type": "function_call_output",
                    "call_id": output_item.call_id,
                    "output": json.dumps(result),
                }
            )
        return tool_outputs

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
        """Return available configured models and their reasoning levels."""
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
    
    async def _create_conversation(self, user_id: str) -> str:
        conversation = await self.client.conversations.create()
        self.user_conversations.update_conversation(user_id, conversation.id)
        return conversation.id
