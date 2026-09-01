import json
from collections.abc import Iterable
from openai import AsyncOpenAI
from ..API.api_client import ApiClient
from bot.tools.tool import tool as Tool
from .prompts import assistant_prompt
import discord
from ....user_conversations import UserConversations
from ....user import User
from ....token_usage import TokenUsage


class AskOpenAI(ApiClient):
    API_KEY_ENV_VAR = "API_KEY"

    def __init__(
        self,
        tools: Iterable[Tool] = (),
        client: AsyncOpenAI | None = None,
        user_conversations: UserConversations | None = None,
        token_usage: TokenUsage | None = None,
    ):
        self._tools_by_name = {}
        self._tool_definitions = []
        self.user_conversations = user_conversations or UserConversations()
        self.token_usage = token_usage or TokenUsage()
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

    async def ask_openai(self, prompt: str, ctx: discord.ApplicationContext) -> str:
        user_id = User(ctx).get_discord_id()
        conversation_id = self.user_conversations.get_conversation(user_id)

        if conversation_id is None:
            conversation = await self.client.conversations.create()
            conversation_id = conversation.id
            self.user_conversations.update_conversation(user_id, conversation_id)

        request = {
            "model": "gpt-5.6-luna",
            "input": assistant_prompt(prompt),
            "conversation": conversation_id,
        }
        if self._tool_definitions:
            request["tools"] = self._tool_definitions
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
            response = await self.client.responses.create(
                model="gpt-5.6-luna",
                previous_response_id=response.id,
                input=tool_outputs,
                tools=self._tool_definitions,
            )

            self._record_usage(user_id, response)

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
