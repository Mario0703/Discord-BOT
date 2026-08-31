import asyncio
from unittest.mock import AsyncMock, Mock

from bot.modules.client.openAI.askingOpenAI import AskOpenAI


def test_ask_openai():
    mock_client = Mock()
    mock_response = Mock(output_text="Hello from the test")
    mock_client.responses.create = AsyncMock(return_value=mock_response)

    result = asyncio.run(AskOpenAI(client=mock_client).ask_openai("Say hello"))

    assert result == "Hello from the test"
    mock_client.responses.create.assert_called_once_with(
        model="gpt-5.6-luna",
        input="Say hello",
    )
