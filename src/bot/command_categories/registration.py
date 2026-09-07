import logging
from datetime import datetime, timedelta, timezone

import discord

from bot.command_categories.assistant import register as register_assistant
from bot.command_categories.general import register as register_general
from bot.command_categories.technical import register as register_technical
from bot.command_categories.voice_assistant import register as register_voice
from bot.errors import (
    AccessDenied,
    ApplicationError,
)
from bot.modules.client.elevenlabs.elevenlabs import ElevenLabsClient
from bot.modules.client.openai.orchestration import (
    AssistantService,
    ModelPreferenceService,
)
from bot.modules.client.openai.tool_calls.code_review import CodeReview
from bot.modules.client.openai.tool_calls.summary import SummaryOpenAI
from bot.modules.client.openai.tool_calls.top_deals import TopDealsService
from bot.modules.client.openai.tool_calls.transcript import Transcript
from bot.settings.settings import Settings
from bot.storage.token_usage import TokenUsage
from bot.tools.message_formatting import MessageFormatting


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
    settings: Settings,
    assistant_service: AssistantService,
    model_preferences: ModelPreferenceService,
    token_usage: TokenUsage,
    top_deals_service: TopDealsService,
    code_review_service: CodeReview,
    summary_service: SummaryOpenAI,
    transcript_service: Transcript,
    elevenlabs_service: ElevenLabsClient,
) -> None:

    register_assistant(
        bot,
        assistant_service,
        model_preferences,
        top_deals_service,
        settings,
    )
    register_general(bot, summary_service, settings, summary_date_range)
    register_technical(
        bot,
        token_usage,
        code_review_service,
        settings,
        format_code_review,
    )
    register_voice(
        bot,
        transcript_service,
        elevenlabs_service,
        settings,
    )

    @bot.slash_command(
        name="help",
        description="Show all available bot commands",
        guild_ids=list(settings.guild_ids),
    )
    async def help_command(ctx: discord.ApplicationContext) -> None:
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
                value=getattr(command, "description", "No description available."),
                inline=False,
            )

        await MessageFormatting.send_response_embed(ctx, embed)

    @bot.event
    async def on_application_command_error(
        ctx: discord.ApplicationContext, error: discord.DiscordException
    ) -> None:
        original = getattr(error, "original", error)
        if isinstance(original, ApplicationError):
            message = str(original)
        elif isinstance(original, discord.Forbidden):
            message = str(
                AccessDenied(
                    "The bot does not have permission to complete this command."
                )
            )
        else:
            logging.getLogger(__name__).error(
                "Command failed (%s)", type(original).__name__
            )
            message = "I could not complete this command. Please try again later."
        if ctx.interaction.response.is_done():
            await MessageFormatting.send_followup(ctx, message, ephemeral=True)
        else:
            await MessageFormatting.send_response(ctx, message, ephemeral=True)

    @bot.event
    async def on_ready() -> None:
        logging.getLogger(__name__).info("%s is ready and online", bot.user)
