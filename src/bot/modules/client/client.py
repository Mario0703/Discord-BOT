import asyncio
import os

import discord
from dotenv import load_dotenv

from .openAI.askingOpenAI import AskOpenAI
from bot.tools.gamesDeal import GamesDealTool

load_dotenv()  # load all the variables from the env file
bot = discord.Bot()
server_id = 770744107559682108
max_messages_upperbond = 2000

# Composition root: register every tool the assistant is allowed to use here.
openai_service = AskOpenAI(
    tools=[
        GamesDealTool(),
    ]
)


# Bot lifecycle events
@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")


# Slash commands
@bot.slash_command(
    name="ask_openai",
    description="Ask luna some stuff",
    guild_ids=[server_id],
)
async def ask_openai(
    ctx: discord.ApplicationContext,
    question: str,
):
    await ctx.defer()

    answer = await asyncio.to_thread(
        openai_service.ask_openai,
        question,
    )

    await ctx.followup.send(answer[:max_messages_upperbond])


@bot.slash_command(
    name="deals",
    description="Get information on Steam deals",
    guild_ids=[server_id],
)
async def deals(ctx: discord.ApplicationContext):
    await ctx.defer()

    deals_text = await asyncio.to_thread(openai_service.ask_openai_about_good_deals)

    for start in range(0, len(deals_text), max_messages_upperbond):
        await ctx.followup.send(deals_text[start : start + max_messages_upperbond])


@bot.slash_command(
    name="hello",
    description="Say hello to the bot",
)
async def hello(ctx: discord.ApplicationContext):
    await ctx.respond("Hi")


def run_bot():
    bot.run(os.getenv("TOKEN"))


if __name__ == "__main__":
    run_bot()
