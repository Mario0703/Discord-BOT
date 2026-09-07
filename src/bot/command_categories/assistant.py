import discord

from bot.errors import OptionalFeatureUnavailableError, ToolCallLimitError
from bot.Settings.settings import Settings

from ..tools.message_formatting import MessageFormatting


def register(
    bot,
    assistant_service,
    model_preferences,
    top_deals_service,
    settings: Settings,
):
    assistant = bot.create_group(
        "assistant", "AI assistant commands", guild_ids=settings.guild_ids
    )

    @assistant.command(name="ask", description="Ask Luna a question")
    async def ask_openai(ctx: discord.ApplicationContext, question: str):
        await ctx.defer()
        try:
            answer = await assistant_service.get_response(question, ctx.author.id)
        except ToolCallLimitError as error:
            await MessageFormatting.send_followup(ctx, str(error))
            return
        await MessageFormatting.send_followup(
            ctx, answer, allowed_mentions=discord.AllowedMentions.none()
        )

    @assistant.command(
        name="clear_conversation", description="Clear your Luna conversation history"
    )
    async def clear_conversation(ctx: discord.ApplicationContext):
        cleared = await assistant_service.clear_conversation(ctx.author.id)
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
        try:
            text = await top_deals_service.get_top_steam_deals(ctx.author.id)
        except (OptionalFeatureUnavailableError, ToolCallLimitError) as error:
            await MessageFormatting.send_followup(ctx, str(error))
            return
        await MessageFormatting.send_followup(
            ctx, message=text, allowed_mentions=discord.AllowedMentions.none()
        )

    @assistant.command(name="model", description="List the models available for openAI")
    async def list_models(ctx: discord.ApplicationContext):
        await ctx.defer()
        models = await model_preferences.get_model_info()

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
        selection = model_preferences.set_user_model(
            ctx.author.id,
            model_id,
            reasoning_level,
        )

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
        selection = model_preferences.get_selection(ctx.author.id)

        if selection is None:
            model_id, reasoning_level = model_preferences.resolve(ctx.author.id)
            await MessageFormatting.send_response(
                ctx,
                "You have not selected a model. The bot is using the default: "
                f"`{model_id}` with `{reasoning_level}` reasoning.",
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
