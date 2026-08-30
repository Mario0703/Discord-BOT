from unittest.mock import Mock, patch

from bot.modules.client.API.isThereSuchDeal import Deals


@patch("bot.modules.client.API.isThereSuchDeal.requests.get")
def test_api_request(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = {
        "title": "Example Game",
        "deals": [],
    }
    mock_get.return_value = mock_response

    result = Deals(country="DK").get_steam_deals("test-api-key")

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
            "offset": 0,
            "limit": 20,
            "sort": "-cut",
        },
        headers={"ITAD-API-Key": "test-api-key"},
        timeout=15,
    )
