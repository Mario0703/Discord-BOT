import discord


def register(bot, openai_service, top_deals_service, guild_ids):
    assistant = bot.create_group("assistant", "AI assistant commands", guild_ids=guild_ids)

    @assistant.command(name="ask", description="Ask Luna a question")
    async def ask_openai(ctx: discord.ApplicationContext, question: str):
        await ctx.defer()
        answer = await openai_service.ask_openai(question, ctx)
        await ctx.followup.send(answer[:2000])

    @assistant.command(name="clear_conversation", description="Clear your Luna conversation history")
    async def clear_conversation(ctx: discord.ApplicationContext):
        cleared = await openai_service.clear_conversation(ctx)
        await ctx.respond(
            "Your conversation history has been cleared."
            if cleared else "You do not have any conversation history to clear."
        )

    @assistant.command(name="deals", description="Get the top Steam deals")
    async def deals(ctx: discord.ApplicationContext):
        await ctx.defer()
        text = await top_deals_service.get_top_steam_deals()
        for start in range(0, len(text), 2000):
            await ctx.followup.send(text[start : start + 2000])
