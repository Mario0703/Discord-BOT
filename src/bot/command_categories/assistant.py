import discord


def register(bot, openai_service, top_deals_service, guild_ids):
    assistant = bot.create_group(
        "assistant", "AI assistant commands", guild_ids=guild_ids
    )

    @assistant.command(name="ask", description="Ask Luna a question")
    async def ask_openai(ctx: discord.ApplicationContext, question: str):
        await ctx.defer()
        answer = await openai_service.ask_openai(question, ctx)
        await ctx.followup.send(answer[:2000])

    @assistant.command(
        name="clear_conversation", description="Clear your Luna conversation history"
    )
    async def clear_conversation(ctx: discord.ApplicationContext):
        cleared = await openai_service.clear_conversation(ctx)
        await ctx.respond(
            "Your conversation history has been cleared."
            if cleared
            else "You do not have any conversation history to clear."
        )

    @assistant.command(name="deals", description="Get the top Steam deals")
    async def deals(ctx: discord.ApplicationContext):
        await ctx.defer()
        text = await top_deals_service.get_top_steam_deals()
        for start in range(0, len(text), 2000):
            await ctx.followup.send(text[start : start + 2000])

    @assistant.command(name="model", description="List the models available for openAI")
    async def list_models(ctx: discord.ApplicationContext):
        await ctx.defer()
        models = await openai_service.get_model_info()

        if not models:
            await ctx.followup.send("None of the configured OpenAI models are available.")
            return

        embed = discord.Embed(
            title="Available OpenAI models",
            description="Choose a model, then select one of its supported reasoning levels.",
        )

        for model_id, reasoning_levels in models.items():
            levels = ", ".join(reasoning_levels)
            embed.add_field(
                name=model_id,
                value=f"**Reasoning levels:** {levels}",
                inline=False,
            )
        await ctx.followup.send(embed=embed)
    
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
        success = await openai_service.set_user_model(ctx, model_id, reasoning_level)

        if success:
            await ctx.followup.send(
                f"Model set to `{model_id}` with reasoning level `{reasoning_level}`."
            )
        else:
            await ctx.followup.send(
                "That model and reasoning-level combination is not supported. "
                "Use `/assistant model` to see the available options."
            )

    @assistant.command(
        name="show_my_model",
        description="Show your selected OpenAI model and reasoning level",
    )
    async def show_my_model(ctx: discord.ApplicationContext):
        selection = openai_service.get_user_model(ctx)

        if selection is None:
            await ctx.respond(
                "You have not selected a model. The bot is using the default: "
                "`gpt-5.6-luna` with `medium` reasoning."
            )
            return

        model_id, reasoning_level = selection.get_selection()
        await ctx.respond(
            f"Your selected model is `{model_id}` with reasoning level "
            f"`{reasoning_level}`."
        )
