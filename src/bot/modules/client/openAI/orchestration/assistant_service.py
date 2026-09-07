from bot.Settings.settings import Settings
from bot.storage.token_usage import TokenUsage
from bot.storage.user_conversations import UserConversations

from .model_preference_service import ModelPreferenceService
from .openai_gateway import OpenAIGateway
from .tool_dispatcher import ToolDispatcher


class AssistantService:
    """Coordinate conversations, preferences, tools, and OpenAI responses."""

    def __init__(
        self,
        open_ai_gateway: OpenAIGateway,
        model_preference_service: ModelPreferenceService,
        tool_dispatcher: ToolDispatcher,
        conversations: UserConversations,
        token_usage: TokenUsage,
        settings: Settings,
    ) -> None:
        self.gateway = open_ai_gateway
        self.model_preferences = model_preference_service
        self.tool_dispatcher = tool_dispatcher
        self.conversations = conversations
        self.token_usage = token_usage
        self.settings = settings
