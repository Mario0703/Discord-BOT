import asyncio
from datetime import datetime, timedelta

import discord

from bot.Settings.settings import Settings

from ..tools.message_formatting import MessageFormatting


def _validate_summary_dates(
    start: str,
    end: str,
    summary_date_range,
    settings: Settings,
) -> tuple[datetime, datetime, str | None]:
    try:
        start_date, end_date = summary_date_range(start, end)
    except ValueError:
        return (
            datetime.min,
            datetime.min,
            "Use ISO dates, for example: `2026-08-31` to `2026-09-01`.",
        )

    current_time = discord.utils.utcnow()
    if start_date > current_time or end_date > current_time:
        return (
            datetime.min,
            datetime.min,
            "You cannot summarize messages from the future.",
        )
    if end_date - start_date > timedelta(days=settings.summary_max_days):
        return (
            datetime.min,
            datetime.min,
            f"The date range cannot exceed {settings.summary_max_days} days.",
        )
    return start_date, end_date, None


def _find_channel(ctx: discord.ApplicationContext, channel_name: str):
    return discord.utils.get(
        ctx.guild.text_channels,
        name=channel_name.removeprefix("#"),
    )


async def _collect_summary_messages(
    channel, start_date, end_date, settings: Settings
) -> tuple[str, str | None]:
    messages = []
    async for message in channel.history(
        after=start_date,
        before=end_date,
        oldest_first=True,
        limit=settings.summary_max_messages + 1,
    ):
        messages.append(
            f"[{message.created_at.isoformat()}] {message.author}: {message.content}"
        )

    if len(messages) > settings.summary_max_messages:
        return "", (
            "The number of messages exceeds the limit of "
            f"{settings.summary_max_messages}. "
            "Please narrow down the date range."
        )

    transcript = "\n".join(messages) or "No messages found."
    if len(transcript) > settings.summary_max_characters:
        return "", (
            f"The summary text exceeds the limit of "
            f"{settings.summary_max_characters:,} characters. "
            "Please narrow down the date range."
        )
    return transcript, None


def register(bot, summary_service, settings: Settings, summary_date_range):
    general = bot.create_group(
        "general", "General bot commands", guild_ids=settings.guild_ids
    )

    @general.command(name="hello", description="Say hello")
    async def hello(ctx: discord.ApplicationContext):
        await MessageFormatting.send_response(ctx, "Hi")

    @general.command(name="summarize", description="Summarize a channel")
    async def summarize(
        ctx: discord.ApplicationContext, start: str, end: str, channel_name: str
    ):
        start_date, end_date, error = _validate_summary_dates(
            start, end, summary_date_range, settings
        )
        if error:
            await MessageFormatting.send_response(
                ctx, error, allowed_mentions=discord.AllowedMentions.none()
            )
            return

        channel = _find_channel(ctx, channel_name)
        if channel is None:
            await MessageFormatting.send_response(
                ctx,
                f"I couldn't find the channel `{channel_name}`.",
                allowed_mentions=discord.AllowedMentions.none(),
            )
            return

        permissions = channel.permissions_for(ctx.author)
        if not (permissions.view_channel and permissions.read_message_history):
            await MessageFormatting.send_response(
                ctx,
                "You do not have permission to view this channel or its history.",
                allowed_mentions=discord.AllowedMentions.none(),
            )
            return

        await ctx.defer()
        messages, error = await _collect_summary_messages(
            channel, start_date, end_date, settings
        )
        if error:
            await MessageFormatting.send_followup(
                ctx, error, allowed_mentions=discord.AllowedMentions.none()
            )
            return
        summary = await summary_service.summerice_channel_history_start_to_end(
            channel.name, start, end, messages, ctx
        )
        await MessageFormatting.send_followup(
            ctx,
            summary,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @general.command(
        name="reminder", description="I will remind you to check something"
    )
    async def reminder(ctx: discord.ApplicationContext, seconds: int, message: str):
        await MessageFormatting.send_response(
            ctx,
            f"Okay, I will remind you in {seconds} seconds.",
            allowed_mentions=discord.AllowedMentions.none(),
        )
        await asyncio.sleep(seconds)
        try:
            await MessageFormatting.send_direct_message(
                ctx.author,
                f"Reminder: {message}",
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except discord.Forbidden:
            await MessageFormatting.send_followup(
                ctx,
                "I couldn't DM you.",
                allowed_mentions=discord.AllowedMentions.none(),
            )
