from abc import ABC, abstractmethod
from typing import Any


class tool(ABC):
    name: str
    description: str
    parameters: dict[str, Any]

    @abstractmethod
    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        pass
