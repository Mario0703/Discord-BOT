import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock

from bot.modules.client.openAI.orchestration import (
    AssistantService,
    ModelPreferenceService,
    OpenAIGateway,
    ToolDispatcher,
)
from bot.modules.client.openAI.toolCalls.code_review import CodeReview
from bot.modules.client.openAI.toolCalls.prompts import code_review_prompt
from bot.storage.model_selections import ModelSelectionStore
from bot.storage.token_usage import TokenUsage
from bot.storage.user_conversations import UserConversations
from tests.helpers import make_test_settings


def test_code_review_is_stateless_and_uses_saved_user_profile(tmp_path: Path):
    client = Mock()
    client.responses.create = AsyncMock(
        return_value=Mock(
            output_text="Review complete",
            output=[],
            usage=Mock(input_tokens=10, output_tokens=5),
        )
    )
    settings = make_test_settings()
    gateway = OpenAIGateway(client=client)
    selections = ModelSelectionStore(tmp_path / "models.json")
    selections.set_selection(12345, "gpt-5.6-terra", "high")
    usage = TokenUsage(tmp_path / "usage.json")
    assistant = AssistantService(
        gateway,
        ModelPreferenceService(gateway, selections, settings),
        ToolDispatcher(),
        UserConversations(tmp_path / "conversations.json"),
        usage,
        settings,
    )
    service = CodeReview(assistant)

    result = asyncio.run(
        service.do_code_review("python", "print('hello')", 12345)
    )

    assert result == "Review complete"
    request = client.responses.create.await_args.kwargs
    assert request["model"] == "gpt-5.6-terra"
    assert request["reasoning"] == {"effort": "high"}
    assert request["conversation"] is None
    assert request["tools"] == []
    assert request["input"] == code_review_prompt("python", "print('hello')")
    assert usage.report() == {"12345": {"input": 10, "output": 5}}
