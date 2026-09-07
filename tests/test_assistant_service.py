import asyncio
from unittest.mock import AsyncMock, Mock

from bot.modules.client.openai.orchestration import AssistantService
from bot.storage.token_usage import TokenUsage
from bot.storage.user_conversations import UserConversations
from tests.helpers import make_test_settings


def _service(tmp_path, gateway, dispatcher) -> AssistantService:
    preferences = Mock()
    preferences.resolve.return_value = ("gpt-5.6-luna", "medium")
    return AssistantService(
        open_ai_gateway=gateway,
        model_preference_service=preferences,
        tool_dispatcher=dispatcher,
        conversations=UserConversations(tmp_path / "conversations.json"),
        token_usage=TokenUsage(tmp_path / "usage.json"),
        settings=make_test_settings(),
    )


def test_conversations_are_isolated_by_workflow(tmp_path):
    gateway = Mock()
    gateway.create_conversation = AsyncMock(
        side_effect=["conv_assistant", "conv_review"]
    )
    gateway.create_response = AsyncMock(
        return_value=Mock(output=[], output_text="Done", usage=None)
    )
    dispatcher = Mock()
    dispatcher.get_tool_definitions.return_value = []
    dispatcher.execute_tool_calls = AsyncMock(return_value=[])
    service = _service(tmp_path, gateway, dispatcher)

    async def run_requests():
        await service.generate_response("Hello", 123, workflow="assistant")
        await service.generate_response("Review", 123, workflow="code_review")

    asyncio.run(run_requests())

    calls = gateway.create_response.await_args_list
    assert calls[0].kwargs["conversation_id"] == "conv_assistant"
    assert calls[1].kwargs["conversation_id"] == "conv_review"


def test_stateless_tool_follow_up_uses_previous_response_id(tmp_path):
    tool_call = Mock(type="function_call")
    first_response = Mock(id="response_1", output=[tool_call], usage=None)
    final_response = Mock(id="response_2", output=[], output_text="Done", usage=None)
    gateway = Mock()
    gateway.create_response = AsyncMock(side_effect=[first_response, final_response])
    dispatcher = Mock()
    dispatcher.get_tool_definitions.return_value = []
    dispatcher.execute_tool_calls = AsyncMock(
        side_effect=[[{"type": "function_call_output"}], []]
    )
    service = _service(tmp_path, gateway, dispatcher)

    response = asyncio.run(
        service.create_response_without_conversation(
            "Hello",
            "gpt-5.6-luna",
            "medium",
        )
    )

    assert response is final_response
    follow_up = gateway.create_response.await_args_list[1].kwargs
    assert follow_up["previous_response_id"] == "response_1"
    assert follow_up["conversation_id"] is None
