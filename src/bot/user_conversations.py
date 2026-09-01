import json
from pathlib import Path


class UserConversations:
    def __init__(self, file_path="user_conversations.json"):
        self.file_path = Path(file_path)
        self.conversations = self._load()

    def _load(self):
        if not self.file_path.exists():
            return {}

        with self.file_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _save(self):
        with self.file_path.open("w", encoding="utf-8") as file:
            json.dump(self.conversations, file, indent=2)

    def get_conversation(self, user_id):
        user_id = str(user_id)
        return self.conversations.get(user_id)

    def update_conversation(self, user_id, conversation_id):
        user_id = str(user_id)
        self.conversations[user_id] = conversation_id
        self._save()

    def remove_conversation(self, user_id):
        user_id = str(user_id)
        conversation_id = self.conversations.pop(user_id, None)

        if conversation_id is not None:
            self._save()

        return conversation_id
