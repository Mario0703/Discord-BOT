import asyncio
import discord
import os  # default module
from dotenv import load_dotenv
from .API.isThereSuchDeal import Deals
from .openAI.askingOpenAI import AskOpenAI

load_dotenv()  # load all the variables from the env file
bot = discord.Bot()


@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")


@bot.slash_command(
    name="hello",
    description="Say hello to the bot",
)
async def hello(ctx: discord.ApplicationContext):
    await ctx.respond("Hi")


@bot.slash_command(
    name="ask_openai",
    description="Ask luna some stuff",
    guild_ids=[770744107559682108],
)
async def askOpenAI(ctx: discord.ApplicationContext):
    question = AskOpenAI().ask_openai()
    await ctx.respond(question)


@bot.slash_command(
    name="deals",
    description="Get information on Steam deals",
    guild_ids=[770744107559682108],
)
async def deals(ctx: discord.ApplicationContext):
    await ctx.defer()

    deals_text = await asyncio.to_thread(
        AskOpenAI().ask_openai_about_good_deals
    )

    for start in range(0, len(deals_text), 2000):
        await ctx.followup.send(deals_text[start:start + 2000])


def run_bot():
    bot.run(os.getenv("TOKEN"))


if __name__ == "__main__":
    run_bot()
