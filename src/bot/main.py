import discord

from .commands import register_commands
from .modules.client.openAI.askingOpenAI import AskOpenAI
from .modules.client.openAI.codeReview import CodeReview
from .modules.client.openAI.topDeals import TopDealsService
from .tools.gamesDeal import GamesDealTool
from .tools.weatherTool import WeatherTool


def create_bot() -> discord.Bot:
    """Create and configure the Discord bot."""
    bot = discord.Bot()

    game_deals_tool = GamesDealTool()
    weather_tool = WeatherTool()
    openai_service = AskOpenAI(tools=[game_deals_tool, weather_tool])
    top_deals_service = TopDealsService(openai_service.client, game_deals_tool)
    code_review_service = CodeReview(openai_service.client)

    register_commands(bot, openai_service, top_deals_service, code_review_service)
    return bot
