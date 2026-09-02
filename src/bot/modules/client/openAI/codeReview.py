import discord
from openai import AsyncOpenAI

from ....model_selections import ModelSelectionStore, resolve_model_settings
from ....user import User
from .prompts import code_review_prompt


class CodeReview:
    def __init__(
        self,
        client: AsyncOpenAI,
        model_selection_store: ModelSelectionStore | None = None,
    ):
        self.client = client
        self.model_selection_store = model_selection_store or ModelSelectionStore()

    async def do_code_review_with_promt(
        self,
        language: str,
        code: str,
        ctx: discord.ApplicationContext,
    ) -> str:
        user_id = User(ctx).get_discord_id()
        selection = self.model_selection_store.get_selection(user_id)
        model_id, reasoning_level = resolve_model_settings(selection)
        request = {
            "model": model_id,
            "input": code_review_prompt(language, code),
        }
        if reasoning_level is not None:
            request["reasoning"] = {"effort": reasoning_level}

        response = await self.client.responses.create(**request)
        return response.output_text
