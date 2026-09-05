import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
from openai import BadRequestError, NotFoundError

from bot.model_selections import ModelSelectionStore
from bot.modules.client.openAI.askingOpenAI import OpenAiCLientImpl
from bot.token_usage import TokenUsage
from bot.user_conversations import UserConversations


@pytest.mark.parametrize("tool_status", ["success", "unknown", "failure"])
def test_ask_openai_completes_tool_calls(tmp_path: Path, tool_status: str):
    tool = Mock()
    tool.name = "get_weather"
    tool.definition.return_value = {"type": "function", "name": tool.name}
    tool.execute = AsyncMock(return_value={"temperature": 20})
    if tool_status == "failure":
        tool.execute.side_effect = ValueError("Weather unavailable")
    tool_call = Mock(
        type="function_call", call_id="call_weather", arguments='{"city": "Oslo"}'
    )
    tool_call.name = "missing" if tool_status == "unknown" else tool.name
    mock_client = Mock()
    mock_client.responses.create = AsyncMock(side_effect=[
        Mock(output=[Mock(type="reasoning"), tool_call],
             usage=Mock(input_tokens=10, output_tokens=5)),
        Mock(output=[], output_text="Done", usage=Mock(input_tokens=4, output_tokens=2)),
    ])
    conversations = UserConversations(tmp_path / "conversations.json")
    conversations.update_conversation(12345, "conv_existing")
    service = OpenAiCLientImpl(
        tools=[tool], client=mock_client, user_conversations=conversations,
        token_usage=TokenUsage(tmp_path / "usage.json"),
        model_selection_store=ModelSelectionStore(tmp_path / "models.json"),
    )

    result = asyncio.run(
        service.generate_repsone_from_openAI("Weather?", Mock(author=Mock(id=12345)))
    )

    assert result == "Done"
    follow_up = mock_client.responses.create.await_args_list[1].kwargs
    assert follow_up["conversation"] == "conv_existing"
    assert follow_up["tools"] == [tool.definition.return_value]
    assert follow_up["reasoning"] == {"effort": "medium"}
    expected_result = {"temperature": 20}
    if tool_status == "unknown":
        expected_result = {"error": "Unknown tool: missing"}
        tool.execute.assert_not_awaited()
    else:
        tool.execute.assert_awaited_once_with(city="Oslo")
        if tool_status == "failure":
            expected_result = {"error": "Weather unavailable"}
    assert follow_up["input"] == [{
        "type": "function_call_output", "call_id": "call_weather",
        "output": json.dumps(expected_result),
    }]
    assert service.get_token_usage() == (14, 7)


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

    service = OpenAiCLientImpl(
        client=mock_client,
        user_conversations=conversations,
        token_usage=token_usage,
    )
    result = asyncio.run(service.generate_repsone_from_openAI("Say hello", ctx))

    assert result == "Hello from the test"
    mock_client.conversations.create.assert_awaited_once_with()
    mock_client.responses.create.assert_awaited_once_with(
        model="gpt-5.6-luna",
        input="Say hello",
        conversation="conv_test",
        reasoning={"effort": "medium"},
        tools=[],
    )

    saved = UserConversations(tmp_path / "conversations.json")
    assert saved.get_conversation(12345) == "conv_test"
    assert token_usage.report() == {"12345": {"input": 10, "output": 5}}


def test_ask_openai_replaces_a_stale_conversation(tmp_path: Path):
    mock_client = Mock()
    mock_response = Mock(
        output_text="A new conversation was started",
        output=[],
        usage=Mock(input_tokens=10, output_tokens=5),
    )
    stale_response = Mock(status_code=404, request=Mock(), headers={})
    mock_client.responses.create = AsyncMock(
        side_effect=[
            NotFoundError("Conversation not found", response=stale_response, body=None),
            mock_response,
        ]
    )
    mock_client.conversations.create = AsyncMock(return_value=Mock(id="conv_new"))
    ctx = Mock(author=Mock(id=12345))
    conversations = UserConversations(tmp_path / "conversations.json")
    conversations.update_conversation(12345, "conv_stale")

    service = OpenAiCLientImpl(client=mock_client, user_conversations=conversations)
    result = asyncio.run(service.generate_repsone_from_openAI("Say hello", ctx))

    assert result == "A new conversation was started"
    mock_client.conversations.create.assert_awaited_once_with()
    assert mock_client.responses.create.await_count == 2
    assert conversations.get_conversation(12345) == "conv_new"


def test_ask_openai_recovers_from_unanswered_tool_call(tmp_path: Path):
    mock_client = Mock()
    error = BadRequestError(
        "No tool output found for function call call_test.",
        response=Mock(status_code=400, request=Mock(), headers={}),
        body=None,
    )
    mock_client.responses.create = AsyncMock(
        side_effect=[error, Mock(output_text="Recovered", output=[], usage=None)]
    )
    mock_client.conversations.create = AsyncMock(return_value=Mock(id="conv_new"))
    conversations = UserConversations(tmp_path / "conversations.json")
    conversations.update_conversation(12345, "conv_interrupted")
    service = OpenAiCLientImpl(client=mock_client, user_conversations=conversations)

    result = asyncio.run(
        service.generate_repsone_from_openAI("Hello", Mock(author=Mock(id=12345)))
    )

    assert result == "Recovered"
    calls = mock_client.responses.create.await_args_list
    assert len(calls) == 2
    assert calls[0].kwargs["conversation"] == "conv_interrupted"
    assert calls[1].kwargs["conversation"] == "conv_new"
    assert conversations.get_conversation(12345) == "conv_new"


def test_ask_openai_does_not_reset_for_other_bad_requests(tmp_path: Path):
    mock_client = Mock()
    error = BadRequestError(
        "Unsupported reasoning effort",
        response=Mock(status_code=400, request=Mock(), headers={}),
        body=None,
    )
    mock_client.responses.create = AsyncMock(side_effect=error)
    conversations = UserConversations(tmp_path / "conversations.json")
    conversations.update_conversation(12345, "conv_existing")
    service = OpenAiCLientImpl(client=mock_client, user_conversations=conversations)

    with pytest.raises(BadRequestError):
        asyncio.run(
            service.generate_repsone_from_openAI("Hello", Mock(author=Mock(id=12345)))
        )

    mock_client.responses.create.assert_awaited_once()
    mock_client.conversations.create.assert_not_called()
    assert conversations.get_conversation(12345) == "conv_existing"


def test_ask_openai_uses_a_saved_model_selection(tmp_path: Path):
    mock_client = Mock()
    mock_response = Mock(
        output_text="Hello from the test",
        output=[],
        usage=Mock(input_tokens=10, output_tokens=5),
    )
    mock_client.responses.create = AsyncMock(return_value=mock_response)
    mock_client.conversations.create = AsyncMock(return_value=Mock(id="conv_test"))
    ctx = Mock(author=Mock(id=12345))
    selections = ModelSelectionStore(tmp_path / "model_selections.json")
    selections.set_selection(12345, "gpt-5.6-sol", "high")

    service = OpenAiCLientImpl(
        client=mock_client,
        user_conversations=UserConversations(tmp_path / "conversations.json"),
        model_selection_store=selections,
    )
    asyncio.run(service.generate_repsone_from_openAI("Say hello", ctx))

    mock_client.responses.create.assert_awaited_once_with(
        model="gpt-5.6-sol",
        input="Say hello",
        conversation="conv_test",
        reasoning={"effort": "high"},
        tools=[],
    )


def test_set_user_model_saves_only_supported_selections(tmp_path: Path):
    selections = ModelSelectionStore(tmp_path / "model_selections.json")
    service = OpenAiCLientImpl(client=Mock(), model_selection_store=selections)
    ctx = Mock(author=Mock(id=12345))

    saved = asyncio.run(service.set_user_model(ctx, "gpt-5.6-sol", "high"))
    rejected = asyncio.run(service.set_user_model(ctx, "gpt-5.6-sol", "minimal"))

    assert saved is True
    assert rejected is False
    assert selections.get_selection(12345).get_selection() == ("gpt-5.6-sol", "high")


def test_get_user_model_returns_the_saved_selection(tmp_path: Path):
    selections = ModelSelectionStore(tmp_path / "model_selections.json")
    selections.set_selection(12345, "gpt-5.6-terra", "medium")
    service = OpenAiCLientImpl(client=Mock(), model_selection_store=selections)
    ctx = Mock(author=Mock(id=12345))

    selection = service.get_user_model(ctx)

    assert selection is not None
    assert selection.get_selection() == ("gpt-5.6-terra", "medium")
