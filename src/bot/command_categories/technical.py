from collections.abc import Callable

import discord

from bot.errors import AccessDenied, ToolCallLimitError
from bot.modules.client.openai.tool_calls.code_review import CodeReview
from bot.settings.settings import Settings
from bot.storage.token_usage import TokenUsage

from ..tools.message_formatting import MessageFormatting


def _is_administrator(ctx: discord.ApplicationContext) -> bool:
    return (
        ctx.guild is not None
        and getattr(
            ctx.author, "guild_permissions", discord.Permissions.none()
        ).administrator
    )


def register(
    bot: discord.Bot,
    token_usage: TokenUsage,
    code_review_service: CodeReview,
    settings: Settings,
    format_code_review: Callable[[str], str],
) -> None:
    technical = bot.create_group(
        "technical", "Tech related commands", guild_ids=list(settings.guild_ids)
    )

    @technical.command(name="code_review", description="Review source code")
    async def code_review(
        ctx: discord.ApplicationContext, language: str, code: str
    ) -> None:
        await ctx.defer()
        try:
            review = format_code_review(
                await code_review_service.review_code(
                    language,
                    code,
                    ctx.author.id,
                )
            )
        except ToolCallLimitError as error:
            await MessageFormatting.send_followup(ctx, str(error))
            return
        await MessageFormatting.send_followup(
            ctx,
            review,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @technical.command(
        name="token_report",
        description="Get token usage for each user in the last 24 hours",
    )
    async def token_report(ctx: discord.ApplicationContext) -> None:

        if not _is_administrator(ctx):
            raise AccessDenied("Only administrators can use this command.")

        report = token_usage.report()
        if not report:
            await MessageFormatting.send_response(
                ctx,
                "No token usage has been recorded in the last 24 hours.",
                allowed_mentions=discord.AllowedMentions.none(),
            )
            return
        lines = ["Token usage in the last 24 hours:"]
        for user_id, usage in report.items():
            total = usage["input"] + usage["output"]
            lines.append(
                f"<@{user_id}> — input: {usage['input']}, "
                f"output: {usage['output']}, total: {total}"
            )
        await MessageFormatting.send_response(
            ctx,
            "\n".join(lines),
            allowed_mentions=discord.AllowedMentions.none(),
        )
