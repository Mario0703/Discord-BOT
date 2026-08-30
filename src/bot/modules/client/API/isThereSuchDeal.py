import json
import requests


class Deals:
    BASE_URL = "https://api.isthereanydeal.com"

    def get_steam_deals(self, api_key):
        response = requests.get(
            f"{self.BASE_URL}/deals/v2",
            headers={"ITAD-API-Key": api_key},
            params={
                "country": "DK",
                "shops": "61",
                "offset": 0,
                "limit": 20,
                "sort": "-cut",
            },
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

        return data
