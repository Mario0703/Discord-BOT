import discord

from .command_categories.registration import register_pycord_command
from .modules.client.ElevenLabs.elevenlabs import ElevenLabsClient
from .modules.client.openAI.openai_client_impl import OpenAiCLientImpl
from .modules.client.openAI.code_review import CodeReview
from .modules.client.openAI.summary import SummaryOpenAI
from .modules.client.openAI.top_deals import TopDealsService
from .modules.client.openAI.transcript import Transcript
from .tools.games_deal import GamesDealTool
from .tools.weather_tool import WeatherTool


def create_discord_bot() -> discord.Bot:
    intents = discord.Intents.default()
    intents.message_content = True
    bot = discord.Bot(intents=intents)

    game_deals_tool = GamesDealTool()
    weather_tool = WeatherTool()
    openai_service = OpenAiCLientImpl(tools=[game_deals_tool, weather_tool])
    top_deals_service = TopDealsService(openai_service, game_deals_tool)
    code_review_service = CodeReview(openai_service)
    summary_service = SummaryOpenAI(openai_service)
    transcript_service = Transcript(openai_service)
    elevenlabs_service = ElevenLabsClient()

    register_pycord_command(
        bot,
        openai_service,
        top_deals_service,
        code_review_service,
        summary_service,
        transcript_service,
        elevenlabs_service,
    )
    return bot
