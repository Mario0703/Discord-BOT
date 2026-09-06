import json
from collections.abc import Sequence

import requests

from bot.errors import MissingConfigurationError
from bot.Settings.settings import Settings


class Deals:
    BASE_URL = "https://api.isthereanydeal.com"

    AREA_CODES = {
        "AT": "Austria",
        "AU": "Australia",
        "BE": "Belgium",
        "CA": "Canada",
        "CH": "Switzerland",
        "CZ": "Czechia",
        "DE": "Germany",
        "DK": "Denmark",
        "ES": "Spain",
        "FI": "Finland",
        "FR": "France",
        "GB": "United Kingdom",
        "IE": "Ireland",
        "IT": "Italy",
        "JP": "Japan",
        "NL": "Netherlands",
        "NO": "Norway",
        "NZ": "New Zealand",
        "PL": "Poland",
        "PT": "Portugal",
        "SE": "Sweden",
        "TR": "Türkiye",
        "US": "United States",
    }

    SHOP_TITLES = {
        2: "AllYouPlay",
        3: "Amazon",
        13: "DLGamer",
        19: "2game",
        35: "GOG",
        61: "Steam",
    }

    def __init__(
        self,
        country: str,
        shop: str | int,
        discount_range: Sequence[int],
        settings: Settings | None = None,
    ):

        if settings is None:
            raise MissingConfigurationError("Settings are required.")
        if not settings.itad_api_key:
            raise MissingConfigurationError("IsThereAnyDeal API key is required.")

        self.api_key = settings.itad_api_key

        if not isinstance(country, str) or not country.strip():
            raise ValueError("country must be a non-empty string")

        if shop is None or (isinstance(shop, str) and not shop.strip()):
            raise ValueError("shop must be specified")

        if isinstance(discount_range, (str, bytes)):
            raise ValueError("discount_range must contain exactly two integers")
        try:
            if len(discount_range) != 2 or not all(
                isinstance(value, int) for value in discount_range
            ):
                raise ValueError
        except (TypeError, ValueError):
            raise ValueError(
                "discount_range must contain exactly two integers"
            ) from None

        minimum, maximum = discount_range
        if not 0 <= minimum <= maximum <= 100:
            raise ValueError("discount_range must be between 0 and 100")

        self.country = country.strip()
        self.shop = str(shop)
        self.discount_range = (minimum, maximum)

        # Instance-level maps, available to callers as requested.
        self.shops = self.SHOP_TITLES.copy()
        self.areaCode = self.AREA_CODES.copy()

    def get_steam_deals(self):
        response = requests.get(
            f"{self.BASE_URL}/deals/v2",
            headers={"ITAD-API-Key": self.api_key or ""},
            params={
                "country": self.country,
                "shops": self.shop,
                "filter": json.dumps(
                    {
                        "cut": {
                            "min": self.discount_range[0],
                            "max": self.discount_range[1],
                        }
                    }
                ),
                "offset": 0,
                "limit": 20,
                "sort": "-cut",
            },
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

        return data
