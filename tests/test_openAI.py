import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
from openai import BadRequestError, NotFoundError

from bot.errors import InvalidInput, ToolCallLimitError
from bot.modules.client.openai.orchestration import (
    AssistantService,
    ModelPreferenceService,
    OpenAIGateway,
    ToolDispatcher,
)
from bot.storage.model_selections import ModelSelectionStore
from bot.storage.token_usage import TokenUsage
from bot.storage.user_conversations import UserConversations
from tests.helpers import make_test_settings


def _service(
    tmp_path: Path,
    client,
    *,
    tools=None,
    settings=None,
    conversations=None,
    selections=None,
    usage=None,
) -> tuple[AssistantService, ModelPreferenceService]:
    settings = settings or make_test_settings()
    gateway = OpenAIGateway(client=client)
    selections = selections or ModelSelectionStore(tmp_path / "models.json")
    preferences = ModelPreferenceService(gateway, selections, settings)
    assistant = AssistantService(
        gateway,
        preferences,
        ToolDispatcher(tools),
        conversations or UserConversations(tmp_path / "conversations.json"),
        usage or TokenUsage(tmp_path / "usage.json"),
        settings,
    )
    return assistant, preferences


@pytest.mark.parametrize("tool_status", ["success", "unknown", "failure"])
def test_assistant_completes_tool_calls(tmp_path: Path, tool_status: str):
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
    client = Mock()
    client.responses.create = AsyncMock(
        side_effect=[
            Mock(
                output=[Mock(type="reasoning"), tool_call],
                usage=Mock(input_tokens=10, output_tokens=5),
            ),
            Mock(
                output=[],
                output_text="Done",
                usage=Mock(input_tokens=4, output_tokens=2),
            ),
        ]
    )
    conversations = UserConversations(tmp_path / "conversations.json")
    conversations.update_conversation(12345, "conv_existing")
    service, _ = _service(
        tmp_path,
        client,
        tools=[tool],
        conversations=conversations,
    )

    result = asyncio.run(service.generate_response("Weather?", 12345))

    assert result == "Done"
    follow_up = client.responses.create.await_args_list[1].kwargs
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
            expected_result = {
                "error": "The tool could not complete the request. "
                "Please try again later."
            }
    assert follow_up["input"] == [
        {
            "type": "function_call_output",
            "call_id": "call_weather",
            "output": json.dumps(expected_result),
        }
    ]
    assert service.input_token_count == 14
    assert service.output_token_count == 7


def test_assistant_creates_and_saves_conversation(tmp_path: Path):
    client = Mock()
    client.responses.create = AsyncMock(
        return_value=Mock(
            output_text="Hello",
            output=[],
            usage=Mock(input_tokens=10, output_tokens=5),
        )
    )
    client.conversations.create = AsyncMock(return_value=Mock(id="conv_test"))
    conversations = UserConversations(tmp_path / "conversations.json")
    usage = TokenUsage(tmp_path / "usage.json")
    service, _ = _service(
        tmp_path,
        client,
        conversations=conversations,
        usage=usage,
    )

    result = asyncio.run(service.generate_response("Say hello", 12345))

    assert result == "Hello"
    assert conversations.get_conversation(12345) == "conv_test"
    assert usage.report() == {"12345": {"input": 10, "output": 5}}


@pytest.mark.parametrize("recoverable", ["missing", "unanswered_tool"])
def test_assistant_replaces_stale_conversation(tmp_path: Path, recoverable: str):
    client = Mock()
    if recoverable == "missing":
        error = NotFoundError(
            "Conversation not found",
            response=Mock(status_code=404, request=Mock(), headers={}),
            body=None,
        )
    else:
        error = BadRequestError(
            "No tool output found for function call call_test.",
            response=Mock(status_code=400, request=Mock(), headers={}),
            body=None,
        )
    client.responses.create = AsyncMock(
        side_effect=[error, Mock(output_text="Recovered", output=[], usage=None)]
    )
    client.conversations.create = AsyncMock(return_value=Mock(id="conv_new"))
    conversations = UserConversations(tmp_path / "conversations.json")
    conversations.update_conversation(12345, "conv_stale")
    service, _ = _service(tmp_path, client, conversations=conversations)

    result = asyncio.run(service.generate_response("Hello", 12345))

    assert result == "Recovered"
    assert conversations.get_conversation(12345) == "conv_new"
    assert client.responses.create.await_args_list[1].kwargs["conversation"] == (
        "conv_new"
    )


def test_assistant_does_not_reset_for_other_bad_requests(tmp_path: Path):
    client = Mock()
    error = BadRequestError(
        "Unsupported reasoning effort",
        response=Mock(status_code=400, request=Mock(), headers={}),
        body=None,
    )
    client.responses.create = AsyncMock(side_effect=error)
    conversations = UserConversations(tmp_path / "conversations.json")
    conversations.update_conversation(12345, "conv_existing")
    service, _ = _service(tmp_path, client, conversations=conversations)

    with pytest.raises(InvalidInput):
        asyncio.run(service.generate_response("Hello", 12345))

    client.conversations.create.assert_not_called()
    assert conversations.get_conversation(12345) == "conv_existing"


def test_assistant_uses_saved_model_selection(tmp_path: Path):
    client = Mock()
    client.responses.create = AsyncMock(
        return_value=Mock(output_text="Hello", output=[], usage=None)
    )
    client.conversations.create = AsyncMock(return_value=Mock(id="conv_test"))
    selections = ModelSelectionStore(tmp_path / "models.json")
    selections.set_selection(12345, "gpt-5.6-sol", "high")
    service, _ = _service(tmp_path, client, selections=selections)

    asyncio.run(service.generate_response("Say hello", 12345))

    request = client.responses.create.await_args.kwargs
    assert request["model"] == "gpt-5.6-sol"
    assert request["reasoning"] == {"effort": "high"}


def test_model_preference_saves_only_supported_selections(tmp_path: Path):
    _, preferences = _service(tmp_path, Mock())

    saved = preferences.set_user_model(12345, "gpt-5.6-sol", "high")
    rejected = preferences.set_user_model(12345, "gpt-5.6-sol", "minimal")

    assert saved is not None
    assert saved.model_name == "gpt-5.6-sol"
    assert saved.reasoning_level == "high"
    assert rejected is None
    assert preferences.get_selection(12345) == saved


def test_assistant_stops_when_tool_call_limit_is_exceeded(tmp_path: Path):
    client = Mock()
    client.responses.create = AsyncMock(
        return_value=Mock(
            output=[
                Mock(type="function_call"),
                Mock(type="function_call"),
            ],
            usage=None,
        )
    )
    conversations = UserConversations(tmp_path / "conversations.json")
    conversations.update_conversation(12345, "conv_existing")
    service, _ = _service(
        tmp_path,
        client,
        settings=make_test_settings(max_tool_calls=1),
        conversations=conversations,
    )

    with pytest.raises(ToolCallLimitError, match="maximum of 1 tool calls"):
        asyncio.run(service.generate_response("Use tools", 12345))
