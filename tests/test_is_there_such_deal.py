import json
from unittest.mock import Mock, patch

from bot.modules.client.api.is_there_such_deal import IsThereAnyDealClient
from bot.settings.settings import Settings


@patch("bot.modules.client.api.is_there_such_deal.requests.get")
def test_api_request(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = {
        "title": "Example Game",
        "deals": [],
    }
    mock_get.return_value = mock_response

    settings = Settings(
        discord_token="test-token",
        openai_api_key="test-openai-key",
        itad_api_key="test-api-key",
    )
    result = IsThereAnyDealClient(
        country="DK",
        shop="61",
        discount_range=(80, 100),
        settings=settings,
    ).get_steam_deals()

    assert result == {
        "title": "Example Game",
        "deals": [],
    }
    mock_response.raise_for_status.assert_called_once_with()
    mock_get.assert_called_once_with(
        "https://api.isthereanydeal.com/deals/v2",
        params={
            "country": "DK",
            "shops": "61",
            "filter": json.dumps({"cut": {"min": 80, "max": 100}}),
            "offset": "0",
            "limit": "20",
            "sort": "-cut",
        },
        headers={"ITAD-API-Key": "test-api-key"},
        timeout=15,
    )
