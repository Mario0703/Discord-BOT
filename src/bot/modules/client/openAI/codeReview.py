import discord

from .askingOpenAI import OpenAiCLientImpl
from .prompts import code_review_prompt


class CodeReview:
    def __init__(self, openai_service: OpenAiCLientImpl):
        self.openai_service = openai_service

    async def do_code_review_with_promt(
        self,
        language: str,
        code: str,
        ctx: discord.ApplicationContext,
    ) -> str:
        prompt = code_review_prompt(language, code)
        return await self.openai_service.generate_repsone_from_openAI(prompt, ctx)
