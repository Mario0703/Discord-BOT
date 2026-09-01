import asyncio
from datetime import datetime, timedelta, timezone

import discord

from bot.modules.client.openAI.askingOpenAI import AskOpenAI
from bot.modules.client.openAI.codeReview import CodeReview
from bot.modules.client.openAI.summary import SummaryOpenAI
from bot.modules.client.openAI.topDeals import TopDealsService

GUILD_IDS = [770744107559682108]
MAX_MESSAGE_LENGTH = 2_000


def format_code_review(review: str) -> str:
    review = review.replace("\\r\\n", "\n").replace("\\n", "\n")
    review = review.replace("```python ", "```python\n")
    review = review.replace("```py ", "```py\n")
    return review.strip()


def summary_date_range(start: str, end: str) -> tuple[datetime, datetime]:
    """Return an inclusive date range suitable for Discord history queries."""
    start_date = datetime.fromisoformat(start)
    end_date = datetime.fromisoformat(end)

    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)

    # A date such as 2026-08-31 means the entire calendar day, not midnight only.
    if "T" not in end and " " not in end:
        end_date += timedelta(days=1)

    if end_date <= start_date:
        raise ValueError("The end date must be after the start date")

    return start_date, end_date


def register_pycord_command(
    bot: discord.Bot,
    openai_service: AskOpenAI,
    top_deals_service: TopDealsService,
    code_review_service: CodeReview,
    summary_service: SummaryOpenAI,
) -> None:

    assistant = bot.create_group(
        "assistant",
        "AI assistant commands",
        guild_ids=GUILD_IDS,
    )

    @assistant.command(name="ask", description="Ask Luna a question")
    async def ask_openai(ctx: discord.ApplicationContext, question: str):
        await ctx.defer()
        answer = await openai_service.ask_openai(question, ctx)
        await ctx.followup.send(answer[:MAX_MESSAGE_LENGTH])

    @assistant.command(
        name="clear_conversation",
        description="Clear your Luna conversation history",
    )
    async def clear_conversation(ctx: discord.ApplicationContext):
        cleared = await openai_service.clear_conversation(ctx)

        if cleared:
            await ctx.respond("Your conversation history has been cleared.")
        else:
            await ctx.respond("You do not have any conversation history to clear.")

    @assistant.command(name="deals", description="Get the top Steam deals")
    async def deals(ctx: discord.ApplicationContext):
        await ctx.defer()
        deals_text = await top_deals_service.get_top_steam_deals()

        for start in range(0, len(deals_text), MAX_MESSAGE_LENGTH):
            await ctx.followup.send(deals_text[start : start + MAX_MESSAGE_LENGTH])

    general = bot.create_group(
        "general",
        "General bot commands",
        guild_ids=GUILD_IDS,
    )

    @general.command(name="hello", description="Say hello")
    async def hello(ctx: discord.ApplicationContext):
        await ctx.respond("Hi")

    @general.command(name="summarize", description="Summarize a channel")
    async def summarize(
        ctx: discord.ApplicationContext,
        start: str,
        end: str,
        channel_name: str,
    ):
        if ctx.guild is None:
            await ctx.respond("This command can only be used in a server.")
            return

        try:
            start_date, end_date = summary_date_range(start, end)
        except ValueError:
            await ctx.respond(
                "Use ISO dates, for example: `2026-08-31` to `2026-08-31`."
            )
            return

        selected_channel = discord.utils.get(
            ctx.guild.text_channels,
            name=channel_name.removeprefix("#"),
        )
        if selected_channel is None:
            await ctx.respond(f"I couldn't find the channel `{channel_name}`.")
            return

        await ctx.defer()
        messages = []
        async for message in selected_channel.history(
            limit=None, after=start_date, before=end_date, oldest_first=True
        ):
            messages.append(
                f"[{message.created_at.isoformat()}] {message.author}: {message.content}"
            )
            print("Content:", message.content)

        summary = await summary_service.summerice_channel_history_start_to_end(
            selected_channel.name,
            start,
            end,
            "\n".join(messages) or "No messages found.",
        )

        for position in range(0, len(summary), MAX_MESSAGE_LENGTH):
            await ctx.followup.send(
                summary[position : position + MAX_MESSAGE_LENGTH],
                allowed_mentions=discord.AllowedMentions.none(),
            )

    @general.command(
        name="reminder", description="I will remind you to check something"
    )
    async def reminder(ctx: discord.ApplicationContext, seconds: int, message: str):
        await ctx.respond(f"Okay, I’ll remind you in {seconds} seconds.")

        await asyncio.sleep(seconds)

        try:
            await ctx.author.send(f"Reminder: {message}")
        except discord.Forbidden:
            await ctx.respond(f"{ctx.author.mention}, I couldn't DM you.")

    technical = bot.create_group(
        "technical", "Tech related commands", guild_ids=GUILD_IDS
    )

    @technical.command(name="code_review", description="Review source code")
    async def code_review(
        ctx: discord.ApplicationContext,
        language: str,
        code: str,
    ):
        await ctx.defer()
        review = await code_review_service.do_code_review_with_promt(language, code)
        review = format_code_review(review)

        for start in range(0, len(review), MAX_MESSAGE_LENGTH):
            await ctx.followup.send(
                review[start : start + MAX_MESSAGE_LENGTH],
                allowed_mentions=discord.AllowedMentions.none(),
            )
    @technical.command(name="Token rapport", description="Get the input and output token that each user has used in the last 24 hours")
    async def token_rapport(ctx: discord.ApplicationContext):
        # Implementation for token rapport command
        pass

    @bot.event
    async def on_ready():
        print(f"{bot.user} is ready and online!")
