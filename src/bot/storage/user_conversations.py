import json
from pathlib import Path
from typing import cast


class UserConversations:
    def __init__(self, file_path: str | Path = "user_conversations.json") -> None:
        self.file_path = Path(file_path)
        self.conversations = self._load()

    def _load(self) -> dict[str, str]:
        if not self.file_path.exists():
            return {}

        with self.file_path.open("r", encoding="utf-8") as file:
            return cast(dict[str, str], json.load(file))

    def _save(self) -> None:
        with self.file_path.open("w", encoding="utf-8") as file:
            json.dump(self.conversations, file, indent=2)

    @staticmethod
    def _key(user_id: str | int, workflow: str) -> str:
        user_id = str(user_id)
        return user_id if workflow == "assistant" else f"{workflow}:{user_id}"

    def get_conversation(
        self,
        user_id: str | int,
        workflow: str = "assistant",
    ) -> str | None:
        return self.conversations.get(self._key(user_id, workflow))

    def update_conversation(
        self,
        user_id: str | int,
        conversation_id: str,
        workflow: str = "assistant",
    ) -> None:
        self.conversations[self._key(user_id, workflow)] = conversation_id
        self._save()

    def remove_conversation(
        self,
        user_id: str | int,
        workflow: str = "assistant",
    ) -> str | None:
        conversation_id = self.conversations.pop(self._key(user_id, workflow), None)

        if conversation_id is not None:
            self._save()

        return conversation_id
