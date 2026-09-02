import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock

from bot.model_selections import ModelSelectionStore
from bot.modules.client.openAI.codeReview import CodeReview


def test_code_review_uses_the_saved_user_profile(tmp_path: Path):
    mock_client = Mock()
    mock_client.responses.create = AsyncMock(
        return_value=Mock(output_text="Review complete")
    )
    selections = ModelSelectionStore(tmp_path / "model_selections.json")
    selections.set_selection(12345, "gpt-5.6-terra", "high")
    service = CodeReview(mock_client, selections)
    ctx = Mock(author=Mock(id=12345))

    result = asyncio.run(
        service.do_code_review_with_promt("python", "print('hello')", ctx)
    )

    assert result == "Review complete"
    request = mock_client.responses.create.await_args.kwargs
    assert request["model"] == "gpt-5.6-terra"
    assert request["reasoning"] == {"effort": "high"}
