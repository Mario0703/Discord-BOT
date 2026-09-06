import asyncio
from datetime import timedelta
from types import SimpleNamespace

import discord

from bot.command_categories.general import (
    _collect_summary_messages,
    _validate_summary_dates,
)
from tests.helpers import make_test_settings


class FakeChannel:
    def __init__(self, messages):
        self.messages = messages
        self.requested_limit = None

    async def history(self, **kwargs):
        self.requested_limit = kwargs["limit"]
        for message in self.messages:
            yield message


def _message(content: str):
    return SimpleNamespace(
        created_at=discord.utils.utcnow(),
        author="test-user",
        content=content,
    )


def test_custom_summary_date_limit_is_enforced():
    end_date = discord.utils.utcnow() - timedelta(days=1)
    start_date = end_date - timedelta(days=2)
    settings = make_test_settings(summary_max_days=1)

    _, _, error = _validate_summary_dates(
        "start",
        "end",
        lambda _start, _end: (start_date, end_date),
        settings,
    )

    assert error == "The date range cannot exceed 1 days."


def test_custom_summary_message_limit_is_enforced():
    channel = FakeChannel([_message("one"), _message("two")])
    settings = make_test_settings(summary_max_messages=1)

    _, error = asyncio.run(
        _collect_summary_messages(
            channel,
            discord.utils.utcnow() - timedelta(days=1),
            discord.utils.utcnow(),
            settings,
        )
    )

    assert channel.requested_limit == 2
    assert "limit of 1" in error


def test_custom_summary_character_limit_is_enforced():
    channel = FakeChannel([_message("message content")])
    settings = make_test_settings(summary_max_characters=10)

    _, error = asyncio.run(
        _collect_summary_messages(
            channel,
            discord.utils.utcnow() - timedelta(days=1),
            discord.utils.utcnow(),
            settings,
        )
    )

    assert "limit of 10 characters" in error
