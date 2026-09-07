import json
from collections.abc import Sequence

import requests

from bot.errors import (
    ExternalServiceUnavailable,
    InvalidInput,
    MissingConfigurationError,
    OptionalFeatureUnavailableError,
)
from bot.settings.settings import Settings

from .payloads import object_payload


class IsThereAnyDealClient:
    BASE_URL = "https://api.isthereanydeal.com"

    def __init__(
        self,
        country: str,
        shop: str | int,
        discount_range: Sequence[int],
        settings: Settings | None = None,
    ) -> None:

        if settings is None:
            raise MissingConfigurationError("Settings are required.")
        if not settings.itad_api_key:
            raise OptionalFeatureUnavailableError(
                "Deals are unavailable because ITAD_API_KEY is not configured."
            )

        self.api_key = settings.itad_api_key

        if not isinstance(country, str) or not country.strip():
            raise InvalidInput("country must be a non-empty string")

        if shop is None or (isinstance(shop, str) and not shop.strip()):
            raise InvalidInput("shop must be specified")

        if isinstance(discount_range, (str, bytes)):
            raise InvalidInput("discount_range must contain exactly two integers")
        try:
            if len(discount_range) != 2 or not all(
                isinstance(value, int) for value in discount_range
            ):
                raise InvalidInput
        except (TypeError, ValueError):
            raise InvalidInput(
                "discount_range must contain exactly two integers"
            ) from None

        minimum, maximum = discount_range
        if not 0 <= minimum <= maximum <= 100:
            raise InvalidInput("discount_range must be between 0 and 100")

        self.country = country.strip()
        self.shop = str(shop)
        self.discount_range = (minimum, maximum)

    def get_steam_deals(self) -> dict[str, object]:
        try:
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
                    "offset": "0",
                    "limit": "20",
                    "sort": "-cut",
                },
                timeout=15,
            )

            response.raise_for_status()

            data = response.json()

            return object_payload(data)
        except (requests.RequestException, ValueError) as error:
            raise ExternalServiceUnavailable(
                "Game deals are temporarily unavailable."
            ) from error
