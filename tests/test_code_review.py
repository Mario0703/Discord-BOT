import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock

from bot.storage.model_selections import ModelSelectionStore
from bot.modules.client.openAI.openai_client_impl import OpenAiCLientImpl
from bot.modules.client.openAI.code_review import CodeReview
from bot.modules.client.openAI.prompts import code_review_prompt
from bot.storage.token_usage import TokenUsage
from bot.storage.user_conversations import UserConversations


def test_code_review_uses_the_saved_user_profile(tmp_path: Path):
    mock_client = Mock()
    mock_client.responses.create = AsyncMock(
        return_value=Mock(
            output_text="Review complete", output=[],
            usage=Mock(input_tokens=10, output_tokens=5),
        )
    )
    selections = ModelSelectionStore(tmp_path / "model_selections.json")
    selections.set_selection(12345, "gpt-5.6-terra", "high")
    conversations = UserConversations(tmp_path / "conversations.json")
    conversations.update_conversation(12345, "conv_existing")
    openai_service = OpenAiCLientImpl(
        client=mock_client,
        model_selection_store=selections,
        user_conversations=conversations,
        token_usage=TokenUsage(tmp_path / "usage.json"),
    )
    service = CodeReview(openai_service)
    ctx = Mock(author=Mock(id=12345))

    result = asyncio.run(
        service.do_code_review_with_promt("python", "print('hello')", ctx)
    )

    assert result == "Review complete"
    request = mock_client.responses.create.await_args.kwargs
    assert request["model"] == "gpt-5.6-terra"
    assert request["reasoning"] == {"effort": "high"}
    assert request["conversation"] == "conv_existing"
    assert request["input"] == code_review_prompt("python", "print('hello')")
    assert openai_service.token_usage.report() == {
        "12345": {"input": 10, "output": 5}
    }
