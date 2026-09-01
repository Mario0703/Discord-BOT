import asyncio
from datetime import timedelta

import discord


def register(bot, summary_service, guild_ids, summary_date_range):
    general = bot.create_group("general", "General bot commands", guild_ids=guild_ids)

    @general.command(name="hello", description="Say hello")
    async def hello(ctx: discord.ApplicationContext):
        await ctx.respond("Hi")

    @general.command(name="summarize", description="Summarize a channel")
    async def summarize(ctx: discord.ApplicationContext, start: str, end: str, channel_name: str):
        if ctx.guild is None:
            await ctx.respond("This command can only be used in a server.")
            return
        try:
            start_date, end_date = summary_date_range(start, end)
        except ValueError:
            await ctx.respond("Use ISO dates, for example: `2026-08-31` to `2026-09-01`.")
            return
        channel = discord.utils.get(ctx.guild.text_channels, name=channel_name.removeprefix("#"))
        if channel is None:
            await ctx.respond(f"I couldn't find the channel `{channel_name}`.")
            return
        await ctx.defer()
        messages = []
        async for message in channel.history(limit=None, after=start_date, before=end_date, oldest_first=True):
            messages.append(f"[{message.created_at.isoformat()}] {message.author}: {message.content}")
        summary = await summary_service.summerice_channel_history_start_to_end(
            channel.name, start, end, "\n".join(messages) or "No messages found."
        )
        for position in range(0, len(summary), 2000):
            await ctx.followup.send(summary[position : position + 2000], allowed_mentions=discord.AllowedMentions.none())

    @general.command(name="reminder", description="I will remind you to check something")
    async def reminder(ctx: discord.ApplicationContext, seconds: int, message: str):
        await ctx.respond(f"Okay, I’ll remind you in {seconds} seconds.")
        await asyncio.sleep(seconds)
        try:
            await ctx.author.send(f"Reminder: {message}")
        except discord.Forbidden:
            await ctx.respond(f"{ctx.author.mention}, I couldn't DM you.")
