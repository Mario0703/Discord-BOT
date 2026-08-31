import os
from abc import ABC


class ApiClient(ABC):
    """Base class for server-side clients that authenticate with one API key."""

    API_KEY_ENV_VAR: str

    def get_api_key(self) -> str:
        """Return this client's configured API key without exposing it in errors."""
        environment_variable = self.API_KEY_ENV_VAR
        api_key = os.getenv(environment_variable)

        if not api_key:
            raise RuntimeError(
                f"Missing required environment variable: {environment_variable}"
            )

        return api_key
