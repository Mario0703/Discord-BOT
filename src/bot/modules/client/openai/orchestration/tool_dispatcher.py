import json
import logging
from typing import cast

from openai.types.responses import Response, ResponseInputParam, ToolParam

from bot.errors import ApplicationError, InvalidInput, ResourceNotFound
from bot.tools.tool import Tool


class ToolDispatcher:
    """Look up tools and serialize their results for OpenAI."""

    def __init__(self, tools: list[Tool] | None = None) -> None:
        self.tools = tools or []

    def get_tool_definitions(self) -> list[ToolParam]:
        return [available_tool.definition() for available_tool in self.tools]

    def find_tool(self, name: str) -> Tool | None:
        for available_tool in self.tools:
            if available_tool.name == name:
                return available_tool
        return None

    async def execute_tool_calls(self, response: Response) -> ResponseInputParam:
        tool_outputs: ResponseInputParam = []
        for output_item in response.output:
            if output_item.type != "function_call":
                continue

            result: dict[str, object]
            try:
                available_tool = self.find_tool(output_item.name)
                if available_tool is None:
                    raise ResourceNotFound(f"Unknown tool: {output_item.name}")
                try:
                    arguments = json.loads(output_item.arguments)
                except json.JSONDecodeError as error:
                    raise InvalidInput("Tool arguments must be valid JSON.") from error
                if not isinstance(arguments, dict):
                    raise InvalidInput("Tool arguments must be a JSON object.")
                result = await available_tool.execute(
                    **cast(dict[str, object], arguments)
                )
            except ApplicationError as error:
                result = {"error": str(error)}
            except Exception as error:
                logging.getLogger(__name__).error(
                    "Tool execution failed (%s)", type(error).__name__
                )
                result = {
                    "error": "The tool could not complete the request. "
                    "Please try again later."
                }

            tool_outputs.append(
                {
                    "type": "function_call_output",
                    "call_id": output_item.call_id,
                    "output": json.dumps(result),
                }
            )
        return tool_outputs
