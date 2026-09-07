import discord

from bot.Settings.settings import Settings

from .command_categories.registration import register_pycord_command
from .modules.client.ElevenLabs.elevenlabs import ElevenLabsClient
from .modules.client.openAI.orchestration import (
    AssistantService,
    ModelPreferenceService,
    OpenAIGateway,
    ToolDispatcher,
)
from .modules.client.openAI.toolCalls.code_review import CodeReview
from .modules.client.openAI.toolCalls.summary import SummaryOpenAI
from .modules.client.openAI.toolCalls.top_deals import TopDealsService
from .modules.client.openAI.toolCalls.transcript import Transcript
from .storage.model_selections import ModelSelectionStore
from .storage.token_usage import TokenUsage
from .storage.user_conversations import UserConversations
from .tools.games_deal import GamesDealTool
from .tools.weather_tool import WeatherTool


def create_discord_bot(settings: Settings) -> discord.Bot:
    intents = discord.Intents.default()
    intents.message_content = True
    bot = discord.Bot(intents=intents)
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    user_conversations = UserConversations(
        settings.data_dir / "user_conversations.json"
    )
    token_usage = TokenUsage(settings.data_dir / "token_usage.json")
    model_selections = ModelSelectionStore(settings.data_dir / "model_selections.json")

    game_deals_tool = GamesDealTool(settings)
    weather_tool = WeatherTool(settings)
    openai_gateway = OpenAIGateway(settings=settings)
    model_preferences = ModelPreferenceService(
        gateway=openai_gateway,
        model_selection_store=model_selections,
        settings=settings,
    )
    tool_dispatcher = ToolDispatcher([game_deals_tool, weather_tool])
    assistant_service = AssistantService(
        open_ai_gateway=openai_gateway,
        model_preference_service=model_preferences,
        tool_dispatcher=tool_dispatcher,
        conversations=user_conversations,
        token_usage=token_usage,
        settings=settings,
    )
    top_deals_service = TopDealsService(assistant_service, game_deals_tool)
    code_review_service = CodeReview(assistant_service)
    summary_service = SummaryOpenAI(assistant_service)
    transcript_service = Transcript(openai_gateway)
    elevenlabs_service = ElevenLabsClient(settings=settings)

    register_pycord_command(
        bot,
        settings,
        assistant_service,
        model_preferences,
        token_usage,
        top_deals_service,
        code_review_service,
        summary_service,
        transcript_service,
        elevenlabs_service,
    )
    return bot
