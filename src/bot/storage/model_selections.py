from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from bot.openai_models import MODEL_REASONING_LEVELS
from bot.Settings.settings import Settings


@dataclass
class ModelSelection:
    model_name: str | None
    reasoning_level: str | None


def resolve_model_settings(
    selection: ModelSelection | None, settings: Settings
) -> tuple[str, str | None]:
    """Use a valid saved selection, otherwise return the bot defaults."""
    default_model = settings.openai_model
    default_reasoning = settings.openai_reasoning_level

    model_id = default_model

    has_valid_model = (
        selection is not None and selection.model_name in MODEL_REASONING_LEVELS
    )
    if has_valid_model:
        model_id = selection.model_name

    supported_levels = MODEL_REASONING_LEVELS.get(model_id, [])
    reasoning_level = default_reasoning

    has_valid_reasoning = (
        selection is not None and selection.reasoning_level in supported_levels
    )
    if has_valid_reasoning:
        reasoning_level = selection.reasoning_level
    elif reasoning_level not in supported_levels:
        reasoning_level = None

    return model_id, reasoning_level


class ModelSelectionStore:
    """Persist each Discord user's OpenAI model selection in a JSON file."""

    def __init__(self, file_path: str | Path = "model_selections.json"):
        self.file_path = Path(file_path)
        self.selections = self._load()

    def _load(self) -> dict[str, ModelSelection]:
        if not self.file_path.exists():
            return {}

        with self.file_path.open("r", encoding="utf-8") as file:
            saved_selections = json.load(file)

        selections = {}
        for user_id, selection in saved_selections.items():
            selections[user_id] = ModelSelection(**selection)

        return selections

    def _save(self) -> None:
        saved_selections = {}

        for user_id, selection in self.selections.items():
            saved_selections[user_id] = asdict(selection)

        with self.file_path.open("w", encoding="utf-8") as file:
            json.dump(saved_selections, file, indent=2)

    def set_selection(
        self,
        user_id: str | int,
        model_name: str,
        reasoning_level: str | None,
    ) -> None:
        self.selections[str(user_id)] = ModelSelection(model_name, reasoning_level)
        self._save()

    def remove_selection(self, user_id: str | int) -> ModelSelection | None:
        selection = self.selections.pop(str(user_id), None)

        if selection is not None:
            self._save()

        return selection
