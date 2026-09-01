import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock

from bot.modules.client.openAI.askingOpenAI import AskOpenAI
from bot.token_usage import TokenUsage
from bot.user_conversations import UserConversations


def test_ask_openai_creates_and_saves_user_conversation(tmp_path: Path):
    mock_client = Mock()
    mock_response = Mock(
        output_text="Hello from the test",
        output=[],
        usage=Mock(input_tokens=10, output_tokens=5),
    )
    mock_client.responses.create = AsyncMock(return_value=mock_response)
    mock_client.conversations.create = AsyncMock(return_value=Mock(id="conv_test"))
    ctx = Mock(author=Mock(id=12345))
    conversations = UserConversations(tmp_path / "conversations.json")
    token_usage = TokenUsage(tmp_path / "token_usage.json")

    service = AskOpenAI(
        client=mock_client,
        user_conversations=conversations,
        token_usage=token_usage,
    )
    result = asyncio.run(service.ask_openai("Say hello", ctx))

    assert result == "Hello from the test"
    mock_client.conversations.create.assert_awaited_once_with()
    mock_client.responses.create.assert_awaited_once_with(
        model="gpt-5.6-luna",
        input="Say hello",
        conversation="conv_test",
    )

    saved = UserConversations(tmp_path / "conversations.json")
    assert saved.get_conversation(12345) == "conv_test"
    assert token_usage.report() == {
        "12345": {"input": 10, "output": 5}
    }
