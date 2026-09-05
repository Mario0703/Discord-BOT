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

    def record(
        self,
        user_id,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        recorded_at = datetime.now(timezone.utc).isoformat()

        usage_record = {
            "user_id": str(user_id),
            "timestamp": recorded_at,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }

        self.records.append(usage_record)
        self._save()

    def report(self, hours: int = 24) -> dict[str, dict[str, int]]:
        "Rapports the token usage for each user within the specified time window (in hours)."
        usage_window_start = datetime.now(timezone.utc) - timedelta(hours=hours)
        usage_by_user: dict[str, dict[str, int]] = {}

        for usage_record in self.records:
            recorded_at = datetime.fromisoformat(usage_record["timestamp"])

            if recorded_at < usage_window_start:
                continue

            user_id = usage_record["user_id"]

            user_usage = usage_by_user.setdefault(
                user_id,
                {
                    "input": 0,
                    "output": 0,
                },
            )

            user_usage["input"] += usage_record["input_tokens"]
            user_usage["output"] += usage_record["output_tokens"]

        return usage_by_user
