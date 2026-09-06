from datetime import datetime, timedelta, timezone
from pathlib import Path

import discord

from bot.command_categories.assistant import register as register_assistant
from bot.command_categories.general import register as register_general
from bot.command_categories.technical import register as register_technical
from bot.command_categories.voice_assistant import register as register_voice
from bot.tools.message_formatting import MessageFormatting

GUILD_IDS = [770744107559682108]
DATA_DIR = Path("data")


def format_code_review(review: str) -> str:
    review = review.replace("\\r\\n", "\n").replace("\\n", "\n")
    review = review.replace("```python ", "```python\n")
    review = review.replace("```py ", "```py\n")
    return review.strip()


def summary_date_range(start: str, end: str) -> tuple[datetime, datetime]:
    start_date = datetime.fromisoformat(start)
    end_date = datetime.fromisoformat(end)
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)
    if "T" not in end and " " not in end:
        end_date += timedelta(days=1)
    if end_date <= start_date:
        raise ValueError("The end date must be after the start date")
    return start_date, end_date


def register_pycord_command(
    bot: discord.Bot,
    openai_service,
    top_deals_service,
    code_review_service,
    summary_service,
    transcript_service,
    elevenlabs_service,
):

    register_assistant(bot, openai_service, top_deals_service, GUILD_IDS)
    register_general(bot, summary_service, GUILD_IDS, summary_date_range)
    register_technical(
        bot, openai_service, code_review_service, GUILD_IDS, format_code_review
    )
    register_voice(
        bot,
        transcript_service,
        elevenlabs_service,
        DATA_DIR,
        GUILD_IDS,
    )

    @bot.slash_command(
        name="help",
        description="Show all available bot commands",
        guild_ids=GUILD_IDS,
    )
    async def help_command(ctx: discord.ApplicationContext):
        embed = discord.Embed(
            title="Available Bot Commands",
            description="Here are the available commands for this bot:",
        )
        embed.set_footer(text="Use /<command> to execute a command.")

        commands = []
        for command in bot.walk_application_commands():
            commands.append(command)

        sorted_commands = sorted(commands, key=lambda item: item.qualified_name)

        for command in sorted_commands:
            embed.add_field(
                name=f"/{command.qualified_name}",
                value=command.description,
                inline=False,
            )

        await MessageFormatting.send_response_embed(ctx, embed)

    @bot.event
    async def on_ready():
        print(f"{bot.user} is ready and online!")
