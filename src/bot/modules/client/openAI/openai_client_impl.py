import json

import discord
from openai import AsyncOpenAI, BadRequestError, NotFoundError

from bot.errors import MissingConfigurationError, ToolCallLimitError
from bot.openai_models import MODEL_REASONING_LEVELS
from bot.Settings.settings import Settings
from bot.tools.tool import tool as Tool

from ....storage.model_selections import (
    ModelSelection,
    ModelSelectionStore,
    resolve_model_settings,
)
from ....storage.token_usage import TokenUsage
from ....storage.user_conversations import UserConversations
from .toolCalls.prompts import assistant_prompt


class OpenAiCLientImpl:
    def __init__(
        self,
        tools: list[Tool] | None = None,
        client: AsyncOpenAI | None = None,
        user_conversations: UserConversations | None = None,
        token_usage: TokenUsage | None = None,
        model_selection_store: ModelSelectionStore | None = None,
        settings: Settings | None = None,
    ):
        if settings is None:
            raise MissingConfigurationError("Settings are required.")
        if not settings.openai_api_key:
            raise MissingConfigurationError("OpenAI API key is required.")

        self.settings = settings
        self.user_conversations = user_conversations or UserConversations()
        self.token_usage = token_usage or TokenUsage()
        self.model_selection_store = model_selection_store or ModelSelectionStore()
        self.input_token_count = 0
        self.output_token_count = 0
        self.tools = tools or []

        if settings.openai_api_key is None:
            raise MissingConfigurationError("OpenAI API key is required.")

        if client is not None:
            self.client = client
        else:
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def generate_repsone_from_openAI(
        self, prompt: str, ctx: discord.ApplicationContext
    ) -> str:
        "Generate a response with the selected model and reasoning level."
        user_id = str(ctx.author.id)
        conversation_id = self.user_conversations.get_conversation(user_id)
        selection = self.model_selection_store.selections.get(str(user_id))
        model_id, reasoning_level = resolve_model_settings(
            selection,
            self.settings,
        )

        if conversation_id is None:
            conversation_id = await self._create_conversation(user_id)

        tool_definitions = self._get_tool_definitions()
        reasoning = None
        if reasoning_level is not None:
            reasoning = {"effort": reasoning_level}

        # Promt the model and get the initial response
        response, conversation_id = await self._create_initial_response(
            user_id, prompt, conversation_id, model_id, tool_definitions, reasoning
        )
        self._record_usage(user_id, response)  # Record initial response usage
        tool_call_count = 0
        while True:
            requested_tool_calls = sum(
                output_item.type == "function_call" for output_item in response.output
            )
            if tool_call_count + requested_tool_calls > self.settings.max_tool_calls:
                raise ToolCallLimitError(
                    "This request exceeded the maximum of "
                    f"{self.settings.max_tool_calls} tool calls. "
                    "Please try a simpler request."
                )

            tool_outputs = await self._execute_tool_calls(response)
            if not tool_outputs:
                return response.output_text
            tool_call_count += len(tool_outputs)

            response = await self.client.responses.create(
                model=model_id,
                conversation=conversation_id,
                input=tool_outputs,
                reasoning=reasoning,
                tools=tool_definitions,
            )
            self._record_usage(user_id, response)  # Record follow-up response usage

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

    async def clear_conversation(self, ctx: discord.ApplicationContext) -> bool:
        user_id = str(ctx.author.id)
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

    async def get_model_info(self) -> dict[str, tuple[str, ...]]:
        available_model_ids = set(await self.get_model_list())
        models_dict = {}

        for model_id, reasoning_levels in MODEL_REASONING_LEVELS.items():
            if model_id in available_model_ids:
                models_dict[model_id] = reasoning_levels

        return models_dict

    def set_user_model(
        self,
        ctx: discord.ApplicationContext,
        model_id: str,
        reasoning_level: str,
    ) -> ModelSelection | None:
        supported_levels = MODEL_REASONING_LEVELS.get(model_id)

        if supported_levels is None or reasoning_level not in supported_levels:
            return None

        user_id = str(ctx.author.id)
        self.model_selection_store.set_selection(
            user_id,
            model_id,
            reasoning_level,
        )
        return self.model_selection_store.selections.get(str(user_id))

    async def _create_conversation(self, user_id: str) -> str:
        conversation = await self.client.conversations.create()
        self.user_conversations.update_conversation(user_id, conversation.id)
        return conversation.id
