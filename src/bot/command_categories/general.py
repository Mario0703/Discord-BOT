import asyncio
from datetime import datetime, timedelta

import discord

from ..tools.message_formatting import MessageFormatting

MAX_MESSAGE_COUNT = 1_000
MAX_CHARACTER_COUNT = 50_000


def _validate_summary_dates(
    start: str, end: str, summary_date_range
) -> tuple[datetime, datetime, str | None]:
    try:
        start_date, end_date = summary_date_range(start, end)
    except ValueError:
        return datetime.min, datetime.min, "Use ISO dates, for example: `2026-08-31` to `2026-09-01`."

    current_time = discord.utils.utcnow()
    if start_date > current_time or end_date > current_time:
        return datetime.min, datetime.min, "You cannot summarize messages from the future."
    if end_date - start_date > timedelta(days=7):
        return datetime.min, datetime.min, "The date range cannot exceed 7 days."
    return start_date, end_date, None


def _find_channel(ctx: discord.ApplicationContext, channel_name: str):
    return discord.utils.get(
        ctx.guild.text_channels,
        name=channel_name.removeprefix("#"),
    )


async def _collect_summary_messages(channel, start_date, end_date) -> tuple[str, str | None]:
    messages = []
    async for message in channel.history(
        after=start_date,
        before=end_date,
        oldest_first=True,
        limit=MAX_MESSAGE_COUNT + 1,
    ):
        messages.append(
            f"[{message.created_at.isoformat()}] {message.author}: {message.content}"
        )

    if len(messages) > MAX_MESSAGE_COUNT:
        return "", (
            f"The number of messages exceeds the limit of {MAX_MESSAGE_COUNT}. "
            "Please narrow down the date range."
        )

    transcript = "\n".join(messages) or "No messages found."
    if len(transcript) > MAX_CHARACTER_COUNT:
        return "", (
            f"The summary text exceeds the limit of {MAX_CHARACTER_COUNT:,} characters. "
            "Please narrow down the date range."
        )
    return transcript, None


def register(bot, summary_service, guild_ids, summary_date_range):
    general = bot.create_group("general", "General bot commands", guild_ids=guild_ids)

    @general.command(name="hello", description="Say hello")
    async def hello(ctx: discord.ApplicationContext):
        await MessageFormatting.send_response(ctx, "Hi")

    @general.command(name="summarize", description="Summarize a channel")
    async def summarize(
        ctx: discord.ApplicationContext, start: str, end: str, channel_name: str
    ):
        start_date, end_date, error = _validate_summary_dates(
            start, end, summary_date_range
        )
        if error:
            await MessageFormatting.send_response(ctx, error)
            return

        channel = _find_channel(ctx, channel_name)
        if channel is None:
            await MessageFormatting.send_response(
                ctx, f"I couldn't find the channel `{channel_name}`."
            )
            return

        permissions = channel.permissions_for(ctx.author)
        if not (permissions.view_channel and permissions.read_message_history):
            await MessageFormatting.send_response(
                ctx,
                "You do not have permission to view this channel or its history.",
            )
            return

        await ctx.defer()
        messages, error = await _collect_summary_messages(
            channel, start_date, end_date
        )
        if error:
            await MessageFormatting.send_followup(ctx, error)
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
            ctx, f"Okay, I’ll remind you in {seconds} seconds."
        )
        await asyncio.sleep(seconds)
        try:
            await MessageFormatting.send_direct_message(
                ctx.author, f"Reminder: {message}"
            )
        except discord.Forbidden:
            await MessageFormatting.send_followup(
                ctx, f"{ctx.author.mention}, I couldn't DM you."
            )
