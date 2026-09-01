from openai import AsyncOpenAI

from .prompts import summary_prompt


class SummaryOpenAI:
    """Create summaries of messages collected from Discord channels."""

    def __init__(self, client: AsyncOpenAI, model: str = "gpt-5.6-luna"):
        self.client = client
        self.model = model

    async def summerice_channel_history_start_to_end(
        self,
        channel_name: str,
        start: str,
        end: str,
        messages: str,
    ) -> str:
        response = await self.client.responses.create(
            model=self.model,
            input=summary_prompt(channel_name, start, end, messages),
        )
        return response.output_text
