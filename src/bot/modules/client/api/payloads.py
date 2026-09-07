"""Validate JSON structure at external service boundaries."""

from typing import cast

from bot.errors import ExternalServiceUnavailable


def object_payload(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ExternalServiceUnavailable("The service returned an invalid object.")
    return cast(dict[str, object], value)


def object_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise ExternalServiceUnavailable("The service returned an invalid list.")
    return [object_payload(item) for item in value]
