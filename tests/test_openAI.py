from unittest.mock import Mock, patch
from bot.modules.client.openAI.res import ask_openai


@patch("bot.modules.client.openAI.res.OpenAI")
def test_ask_openai(mock_openai):
    mock_client = mock_openai.return_value
    mock_response = Mock(output_text="Hello from the test")
    mock_client.responses.create.return_value = mock_response

    result = ask_openai("Say hello")

    assert result == "Hello from the test"
    mock_client.responses.create.assert_called_once_with(
        model="gpt-5.6-luna",
        input="Say hello",
    )
