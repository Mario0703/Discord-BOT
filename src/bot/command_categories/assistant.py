import discord

from bot.Settings.settings import Settings

from ..tools.message_formatting import MessageFormatting


def register(bot, openai_service, top_deals_service, settings: Settings):
    assistant = bot.create_group(
        "assistant", "AI assistant commands", guild_ids=settings.guild_ids
    )

    @assistant.command(name="ask", description="Ask Luna a question")
    async def ask_openai(ctx: discord.ApplicationContext, question: str):
        await ctx.defer()
        answer = await openai_service.generate_repsone_from_openAI(question, ctx)
        await MessageFormatting.send_followup(
            ctx, answer, allowed_mentions=discord.AllowedMentions.none()
        )

    @assistant.command(
        name="clear_conversation", description="Clear your Luna conversation history"
    )
    async def clear_conversation(ctx: discord.ApplicationContext):
        cleared = await openai_service.clear_conversation(ctx)
        response_message = ""

        if cleared:
            response_message = "Your conversation history has been cleared."
        else:
            response_message = "You do not have any conversation history to clear."

        await MessageFormatting.send_followup(
            ctx, response_message, allowed_mentions=discord.AllowedMentions.none()
        )

    @assistant.command(name="deals", description="Get the top Steam deals")
    async def deals(ctx: discord.ApplicationContext):
        await ctx.defer()
        text = await top_deals_service.get_top_steam_deals(ctx)
        await MessageFormatting.send_followup(
            ctx, text, allowed_mentions=discord.AllowedMentions.none()
        )

    @assistant.command(name="model", description="List the models available for openAI")
    async def list_models(ctx: discord.ApplicationContext):
        await ctx.defer()
        models = await openai_service.get_model_info()

        if not models:
            await MessageFormatting.send_followup(
                ctx,
                "None of the configured OpenAI models are available.",
                allowed_mentions=discord.AllowedMentions.none(),
            )
            return

        embed = discord.Embed(
            title="Available OpenAI models",
            description=(
                "Choose a model, then select one of its supported reasoning levels."
            ),
        )

        for model_id, reasoning_levels in models.items():
            levels = ", ".join(reasoning_levels)
            embed.add_field(
                name=model_id,
                value=f"**Reasoning levels:** {levels}",
                inline=False,
            )
        await MessageFormatting.send_followup_embed(ctx, embed)

    @assistant.command(
        name="select_model",
        description="Select a model and reasoning level for your OpenAI interactions",
    )
    async def select_model(
        ctx: discord.ApplicationContext,
        model_id: str,
        reasoning_level: str,
    ):
        await ctx.defer()
        selection = openai_service.set_user_model(ctx, model_id, reasoning_level)

        if selection is not None:
            await MessageFormatting.send_followup(
                ctx,
                f"Model set to `{model_id}` with reasoning level `{reasoning_level}`.",
                allowed_mentions=discord.AllowedMentions.none(),
            )
        else:
            await MessageFormatting.send_followup(
                ctx,
                "That model and reasoning-level combination is not supported. "
                "Use `/assistant model` to see the available options.",
                allowed_mentions=discord.AllowedMentions.none(),
            )

    @assistant.command(
        name="show_my_model",
        description="Show your selected OpenAI model and reasoning level",
    )
    async def show_my_model(ctx: discord.ApplicationContext):
        user_id = str(ctx.author.id)
        selection = openai_service.model_selection_store.selections.get(user_id)

        if selection is None:
            await MessageFormatting.send_response(
                ctx,
                "You have not selected a model. The bot is using the default: "
                "`gpt-5.6-luna` with `medium` reasoning.",
                allowed_mentions=discord.AllowedMentions.none(),
            )
            return

        model_id = selection.model_name
        reasoning_level = selection.reasoning_level
        await MessageFormatting.send_response(
            ctx,
            f"Your selected model is `{model_id}` with reasoning level "
            f"`{reasoning_level}`.",
            allowed_mentions=discord.AllowedMentions.none(),
        )
