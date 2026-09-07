from abc import ABC, abstractmethod

from openai.types.responses import FunctionToolParam

from bot.errors import InvalidInput


class Tool(ABC):
    name: str
    description: str
    parameters: dict[str, object]

    def definition(self) -> FunctionToolParam:
        """Return the OpenAI function-tool schema."""
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "strict": True,
        }

    @abstractmethod
    async def execute(self, **kwargs: object) -> dict[str, object]:
        """Run the tool with model-supplied arguments."""

    @staticmethod
    def string_argument(arguments: dict[str, object], name: str) -> str:
        value = arguments.get(name)
        if not isinstance(value, str):
            raise InvalidInput(f"{name} must be a string.")
        return value

    @staticmethod
    def integer_argument(arguments: dict[str, object], name: str) -> int:
        value = arguments.get(name)
        if not isinstance(value, int) or isinstance(value, bool):
            raise InvalidInput(f"{name} must be an integer.")
        return value
