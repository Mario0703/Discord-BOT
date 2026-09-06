import discord

from ..tools.message_formatting import MessageFormatting


def register(
    bot, openai_service, code_review_service, guild_ids, format_code_review
) -> None:
    technical = bot.create_group(
        "technical", "Tech related commands", guild_ids=guild_ids
    )

    @technical.command(name="code_review", description="Review source code")
    async def code_review(ctx: discord.ApplicationContext, language: str, code: str):
        await ctx.defer()
        review = format_code_review(
            await code_review_service.do_code_review_with_promt(language, code, ctx)
        )
        await MessageFormatting.send_followup(
            ctx,
            review,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @technical.command(
        name="token_report",
        description="Get token usage for each user in the last 24 hours",
    )
    async def token_report(ctx: discord.ApplicationContext):

        if ctx.guild is None or ctx.author.id != ctx.guild.owner_id:
            await MessageFormatting.send_response(
                ctx,
                "Only the server owner can use this command.",
            )
            return

        report = openai_service.token_usage.report()
        if not report:
            await MessageFormatting.send_response(
                ctx, "No token usage has been recorded in the last 24 hours."
            )
            return
        lines = ["Token usage in the last 24 hours:"]
        for user_id, usage in report.items():
            total = usage["input"] + usage["output"]
            lines.append(
                f"<@{user_id}> — input: {usage['input']}, "
                f"output: {usage['output']}, total: {total}"
            )
        await MessageFormatting.send_response(ctx, "\n".join(lines))
