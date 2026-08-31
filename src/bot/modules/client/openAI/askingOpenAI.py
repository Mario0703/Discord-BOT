import asyncio
import json
from collections.abc import Iterable
from typing import Any

from openai import OpenAI
from ..API.api_client import ApiClient
from bot.tools.tool import tool as Tool


class AskOpenAI(ApiClient):
    API_KEY_ENV_VAR = "API_KEY"

    def __init__(self, tools: Iterable[Tool], client: OpenAI | None = None):
        self.client = (
            client if client is not None else OpenAI(api_key=self.get_api_key())
        )
        registered_tools = tuple(tools)
        self._tools_by_name = {tool.name: tool for tool in registered_tools}

        if len(self._tools_by_name) != len(registered_tools):
            raise ValueError("Every registered tool must have a unique name")

        self._tool_definitions: list[dict[str, Any]] = [
            tool.definition() for tool in registered_tools
        ]

    def ask_openai(self, prompt: str) -> str:
        response = self.client.responses.create(
            model="gpt-5.6-luna",
            input=prompt,
            tools=self._tool_definitions,
        )

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
                            "output": json.dumps({"error": f"Unknown tool: {item.name}"}),
                        }
                    )
                    continue

                try:
                    arguments = json.loads(item.arguments)
                    result = asyncio.run(tool.execute(**arguments))
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
            response = self.client.responses.create(
                model="gpt-5.6-luna",
                previous_response_id=response.id,
                input=tool_outputs,
                tools=self._tool_definitions,
            )
