import requests


class Deals:
    BASE_URL = "https://api.isthereanydeal.com"

    def __init__(self, country="DK"):
        self.country = country

    def get_steam_deals(self, api_key):
        response = requests.get(
            f"{self.BASE_URL}/deals/v2",
            params={
                "country": self.country,
                "shops": "61",  # Steam
                "offset": 0,
                "limit": 20,
                "sort": "-cut",
            },
            headers={
                "ITAD-API-Key": api_key,
            },
            timeout=15,
        )

        response.raise_for_status()
        return response.json()
