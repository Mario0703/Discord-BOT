import asyncio

import discord

from bot.modules.client.openAI.askingOpenAI import AskOpenAI
from bot.modules.client.openAI.topDeals import TopDealsService

GUILD_IDS = [770744107559682108]
MAX_MESSAGE_LENGTH = 2_000


def register_commands(
    bot: discord.Bot,
    openai_service: AskOpenAI,
    top_deals_service: TopDealsService,
) -> None:
    """Register grouped slash commands and bot events."""
    assistant = bot.create_group(
        "assistant",
        "AI assistant commands",
        guild_ids=GUILD_IDS,
    )

    @assistant.command(name="ask", description="Ask Luna a question")
    async def ask_openai(ctx: discord.ApplicationContext, question: str):
        await ctx.defer()
        answer = await asyncio.to_thread(openai_service.ask_openai, question)
        await ctx.followup.send(answer[:MAX_MESSAGE_LENGTH])

    @assistant.command(name="deals", description="Get the top Steam deals")
    async def deals(ctx: discord.ApplicationContext):
        await ctx.defer()
        deals_text = await asyncio.to_thread(top_deals_service.get_top_steam_deals)

        for start in range(0, len(deals_text), MAX_MESSAGE_LENGTH):
            await ctx.followup.send(
                deals_text[start : start + MAX_MESSAGE_LENGTH]
            )

    general = bot.create_group(
        "general",
        "General bot commands",
        guild_ids=GUILD_IDS,
    )

    @general.command(name="hello", description="Say hello")
    async def hello(ctx: discord.ApplicationContext):
        await ctx.respond("Hi")

    @bot.event
    async def on_ready():
        print(f"{bot.user} is ready and online!")
