from bot.openai_models import MODEL_REASONING_LEVELS
from bot.Settings.settings import Settings
from bot.storage.model_selections import (
    ModelSelection,
    ModelSelectionStore,
    resolve_model_settings,
)

from .openai_gateway import OpenAIGateway


class ModelPreferenceService:
    """Manage model selections and configured defaults."""

    def __init__(
        self,
        gateway: OpenAIGateway,
        model_selection_store: ModelSelectionStore,
        settings: Settings,
    ) -> None:
        self.gateway = gateway
        self.model_selection_store = model_selection_store
        self.settings = settings

    def resolve(self, user_id: str | int) -> tuple[str, str | None]:
        selection = self.model_selection_store.selections.get(str(user_id))
        return resolve_model_settings(selection, self.settings)

    async def get_model_info(self) -> dict[str, tuple[str, ...]]:
        models = await self.gateway.get_models()
        available_model_ids = {model.id async for model in models}
        return {
            model_id: reasoning_levels
            for model_id, reasoning_levels in MODEL_REASONING_LEVELS.items()
            if model_id in available_model_ids
        }

    def set_user_model(
        self,
        user_id: str | int,
        model_id: str,
        reasoning_level: str,
    ) -> ModelSelection | None:
        supported_levels = MODEL_REASONING_LEVELS.get(model_id)
        if supported_levels is None or reasoning_level not in supported_levels:
            return None

        self.model_selection_store.set_selection(
            user_id,
            model_id,
            reasoning_level,
        )
        return self.model_selection_store.selections.get(str(user_id))
