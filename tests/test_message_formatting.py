import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from bot.tools.message_formatting import MessageFormatting


class MessageFormattingTests(unittest.TestCase):
    def test_split_message_keeps_every_character(self) -> None:
        message = "First line\n" + ("indented code\n" * 200)

        parts = MessageFormatting.split_message(message, limit=100)

        self.assertEqual("".join(parts), message)
        self.assertTrue(all(len(part) <= 100 for part in parts))

    def test_split_message_rejects_invalid_limit(self) -> None:
        with self.assertRaisesRegex(ValueError, "greater than zero"):
            MessageFormatting.split_message("message", limit=0)

    def test_send_response_uses_followups_for_remaining_parts(self) -> None:
        ctx = SimpleNamespace(
            respond=AsyncMock(),
            followup=SimpleNamespace(send=AsyncMock()),
        )
        message = "a" * (MessageFormatting.DISCORD_MESSAGE_LIMIT + 1)

        asyncio.run(MessageFormatting.send_response(ctx, message))

        ctx.respond.assert_awaited_once()
        ctx.followup.send.assert_awaited_once()
        assert ctx.respond.await_args.args == ("a" * 2_000,)
        assert ctx.followup.send.await_args.args == ("a",)
        assert ctx.respond.await_args.kwargs["allowed_mentions"].to_dict() == {
            "parse": []
        }
        assert ctx.followup.send.await_args.kwargs["allowed_mentions"].to_dict() == {
            "parse": []
        }
