from ..orchestration import AssistantService
from .prompts import summary_prompt


class SummaryOpenAI:
    """Create summaries of messages collected from Discord channels."""

    def __init__(self, assistant_service: AssistantService):
        self.assistant_service = assistant_service

    async def summarize_channel_history(
        self,
        channel_name: str,
        start: str,
        end: str,
        messages: str,
        user_id: str | int,
    ) -> str:
        prompt = summary_prompt(channel_name, start, end, messages)
        return await self.assistant_service.get_stateless_response(prompt, user_id)
