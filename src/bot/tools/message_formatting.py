from typing import Any

import discord


class MessageFormatting:
    """Format and send messages while respecting Discord's message limits."""

    DISCORD_MESSAGE_LIMIT = 2_000

    @classmethod
    def split_message(
        cls,
        message: str,
        limit: int = DISCORD_MESSAGE_LIMIT,
    ) -> list[str]:
        """Split a long message into Discord-safe parts at readable boundaries."""
        if limit <= 0:
            raise ValueError("Message limit must be greater than zero.")

        parts: list[str] = []

        while len(message) > limit:
            split_at = message.rfind("\n", 0, limit)
            if split_at >= 0:
                split_at += 1
            else:
                split_at = message.rfind(" ", 0, limit)
                if split_at >= 0:
                    split_at += 1

            if split_at <= 0:
                split_at = limit

            parts.append(message[:split_at])
            message = message[split_at:]

        if message:
            parts.append(message)

        return parts

    @classmethod
    async def send_followup(
        cls,
        ctx: discord.ApplicationContext,
        message: str,
        **kwargs: Any,
    ) -> None:
        """Send a long response as one or more Discord follow-up messages."""
        kwargs.setdefault("allowed_mentions", discord.AllowedMentions.none())
        for part in cls.split_message(message):
            await ctx.followup.send(part, **kwargs)

    @classmethod
    async def send_response(
        cls,
        ctx: discord.ApplicationContext,
        message: str,
        **kwargs: Any,
    ) -> None:
        """Send the first part as a response and remaining parts as follow-ups."""
        kwargs.setdefault("allowed_mentions", discord.AllowedMentions.none())
        parts = cls.split_message(message)
        if not parts:
            return

        await ctx.respond(parts[0], **kwargs)
        for part in parts[1:]:
            await ctx.followup.send(part, **kwargs)

    @staticmethod
    async def send_response_embed(
        ctx: discord.ApplicationContext,
        embed: discord.Embed,
    ) -> None:
        """Send an embed as the initial interaction response."""
        await ctx.respond(
            embed=embed,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @staticmethod
    async def send_followup_embed(
        ctx: discord.ApplicationContext,
        embed: discord.Embed,
    ) -> None:
        """Send an embed after an interaction has been deferred."""
        await ctx.followup.send(
            embed=embed,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @classmethod
    async def send_direct_message(
        cls,
        recipient: discord.abc.Messageable,
        message: str,
        **kwargs: Any,
    ) -> None:
        """Send a Discord-safe message directly to a user or channel."""
        kwargs.setdefault("allowed_mentions", discord.AllowedMentions.none())
        parts = cls.split_message(message)
        if not parts:
            return

        await recipient.send(parts[0], **kwargs)
        for part in parts[1:]:
            await recipient.send(part, **kwargs)
