from bot.errors import InvalidInput

from ..orchestration import AssistantService
from .prompts import code_review_prompt


class CodeReview:
    "Does a code review using the OpenAI service with a language-specific prompt."

    def __init__(self, assistant_service: AssistantService) -> None:
        self.assistant_service = assistant_service

    async def review_code(
        self,
        language: str,
        code: str,
        user_id: str | int,
    ) -> str:
        if not language.strip() or not code.strip():
            raise InvalidInput("Language and code must not be empty.")
        prompt = code_review_prompt(language, code)
        return await self.assistant_service.get_stateless_response(prompt, user_id)
