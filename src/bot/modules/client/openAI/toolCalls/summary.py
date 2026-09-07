import discord

from ..openai_client_impl import OpenAiCLientImpl
from .prompts import summary_prompt


class SummaryOpenAI:
    """Create summaries of messages collected from Discord channels."""

    def __init__(self, openai_service: OpenAiCLientImpl):
        self.openai_service = openai_service

    async def summerice_channel_history_start_to_end(
        self,
        channel_name: str,
        start: str,
        end: str,
        messages: str,
        ctx: discord.ApplicationContext,
    ) -> str:
        prompt = summary_prompt(channel_name, start, end, messages)
        return await self.openai_service.generate_repsone_from_openAI(prompt, ctx)
