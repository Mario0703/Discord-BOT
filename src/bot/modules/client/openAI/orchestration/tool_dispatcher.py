import json

from bot.tools.tool import tool as Tool


class ToolDispatcher:
    """Look up tools and serialize their results for OpenAI."""

    def __init__(self, tools: list[Tool] | None = None) -> None:
        self.tools = tools or []

    def get_tool_definitions(self) -> list[dict]:
        return [available_tool.definition() for available_tool in self.tools]

    def find_tool(self, name: str) -> Tool | None:
        for available_tool in self.tools:
            if available_tool.name == name:
                return available_tool
        return None

    async def execute_tool_calls(self, response) -> list[dict]:
        tool_outputs = []
        for output_item in response.output:
            if output_item.type != "function_call":
                continue

            available_tool = self.find_tool(output_item.name)
            if available_tool is None:
                result = {"error": f"Unknown tool: {output_item.name}"}
            else:
                try:
                    arguments = json.loads(output_item.arguments)
                    if not isinstance(arguments, dict):
                        raise ValueError("Tool arguments must be a JSON object.")
                    result = await available_tool.execute(**arguments)
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
