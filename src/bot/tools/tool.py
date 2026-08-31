from abc import ABC, abstractmethod
from typing import Any


class tool(ABC):
    name: str
    description: str
    parameters: dict[str, Any]

    @abstractmethod
    def definition(self) -> dict[str, Any]:
        """Return the OpenAI function-tool schema."""

    @abstractmethod
    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Run the tool with model-supplied arguments."""
