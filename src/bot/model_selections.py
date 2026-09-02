from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class ModelSelection:
    model_name: str | None
    reasoning_level: str | None

    def get_selection(self) -> tuple[str | None, str | None]:
        return self.model_name, self.reasoning_level

    def set_selection(self, model_name: str, reasoning_level: str | None) -> None:
        self.model_name = model_name
        self.reasoning_level = reasoning_level

    def remove_selection(self) -> None:
        self.model_name = None
        self.reasoning_level = None


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

        return {
            user_id: ModelSelection(**selection)
            for user_id, selection in saved_selections.items()
        }

    def _save(self) -> None:
        saved_selections = {
            user_id: asdict(selection) for user_id, selection in self.selections.items()
        }

        with self.file_path.open("w", encoding="utf-8") as file:
            json.dump(saved_selections, file, indent=2)

    def get_selection(self, user_id: str | int) -> ModelSelection | None:
        return self.selections.get(str(user_id))

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
