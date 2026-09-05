from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


class TokenUsage:
    def __init__(self, file_path="token_usage.json"):
        self.file_path = Path(file_path)
        self.records = self._load()

    def _load(self):
        if not self.file_path.exists():
            return []

        with self.file_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _save(self):
        with self.file_path.open("w", encoding="utf-8") as file:
            json.dump(self.records, file, indent=2)

    def record(self, user_id, input_tokens: int, output_tokens: int):
        self.records.append(
            {
                "user_id": str(user_id),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }
        )
        self._save()

    def report(self, hours: int = 24) -> dict[str, dict[str, int]]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        result: dict[str, dict[str, int]] = {}

        for record in self.records:
            timestamp = datetime.fromisoformat(record["timestamp"])
            if timestamp < cutoff:
                continue

            user_id = record["user_id"]
            usage = result.setdefault(user_id, {"input": 0, "output": 0})
            usage["input"] += record["input_tokens"]
            usage["output"] += record["output_tokens"]

        return result
