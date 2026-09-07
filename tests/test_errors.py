import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import discord
import pytest
import requests
from elevenlabs.core.api_error import ApiError
from openai import APIConnectionError

from bot.errors import (
    AccessDenied,
    ExternalServiceUnavailable,
    InvalidInput,
    ResourceNotFound,
)
from bot.main import create_discord_bot
from bot.modules.client.api.weather import OpenWeather
from bot.modules.client.elevenlabs.elevenlabs import ElevenLabsClient
from bot.modules.client.openai.orchestration import OpenAIGateway, ToolDispatcher
from bot.tools.games_deal import GamesDealTool
from bot.tools.weather_tool import WeatherTool
from tests.helpers import make_test_settings


@pytest.mark.parametrize("payload", ["[]", "null", '"text"', "invalid JSON"])
def test_invalid_tool_arguments_do_not_execute(payload: str) -> None:
    tool = Mock()
    tool.name = "weather"
    tool.execute = AsyncMock()
    call = Mock(type="function_call", arguments=payload, call_id="call_1")
    call.name = tool.name
    outputs = asyncio.run(
        ToolDispatcher([tool]).execute_tool_calls(Mock(output=[call]))
    )
    assert "error" in json.loads(outputs[0]["output"])
    tool.execute.assert_not_awaited()


def test_unexpected_tool_errors_never_leak_provider_details(
    caplog: pytest.LogCaptureFixture,
) -> None:
    tool = Mock()
    tool.name = "weather"
    tool.execute = AsyncMock(side_effect=RuntimeError("secret-key=private"))
    call = Mock(type="function_call", arguments="{}", call_id="call_1")
    call.name = tool.name
    outputs = asyncio.run(
        ToolDispatcher([tool]).execute_tool_calls(Mock(output=[call]))
    )
    assert "secret-key" not in str(outputs)
    assert "secret-key" not in caplog.text
    assert "RuntimeError" in caplog.text


@pytest.mark.parametrize("shop", [True, "61", None])
def test_deals_tool_validates_model_supplied_integers(shop: object) -> None:
    with pytest.raises(InvalidInput, match="shop must be an integer"):
        asyncio.run(
            GamesDealTool(make_test_settings()).execute(
                country="DK",
                shop=shop,
                discount_min=80,
                discount_max=100,
            )
        )


def test_weather_tool_reports_missing_arguments() -> None:
    with pytest.raises(InvalidInput, match="city_name must be a string"):
        asyncio.run(WeatherTool(make_test_settings()).execute())


@pytest.mark.parametrize(
    "failure",
    [
        requests.Timeout("secret URL"),
        requests.HTTPError("secret URL"),
        ValueError("secret body"),
    ],
)
def test_weather_provider_failures_are_safe(failure: Exception) -> None:
    weather = OpenWeather(
        "Oslo", "", "NO", settings=make_test_settings(openweather_api_key="private")
    )
    with patch("bot.modules.client.api.weather.requests.get", side_effect=failure):
        with pytest.raises(
            ExternalServiceUnavailable, match="Weather is temporarily unavailable"
        ) as captured:
            weather.get_weather()
    assert captured.value.__cause__ is failure


@pytest.mark.parametrize(
    "payload, error_type",
    [
        ([], ResourceNotFound),
        ({}, ExternalServiceUnavailable),
        ([{"lat": "invalid", "lon": 10}], ExternalServiceUnavailable),
    ],
)
def test_weather_distinguishes_missing_locations_from_bad_responses(
    payload: object, error_type: type[Exception]
) -> None:
    weather = OpenWeather(
        "Oslo", "", "NO", settings=make_test_settings(openweather_api_key="private")
    )
    response = Mock()
    response.json.return_value = payload
    with patch("bot.modules.client.api.weather.requests.get", return_value=response):
        with pytest.raises(error_type):
            weather.get_weather()


def test_openai_connection_failures_are_translated() -> None:
    failure = APIConnectionError(request=Mock())
    client = Mock()
    client.conversations.create = AsyncMock(side_effect=failure)
    with pytest.raises(ExternalServiceUnavailable) as captured:
        asyncio.run(OpenAIGateway(client=client).create_conversation())
    assert captured.value.__cause__ is failure


def test_elevenlabs_streaming_failure_is_translated(tmp_path: Path) -> None:
    def chunks():
        yield b"audio"
        raise ApiError(status_code=503, body="private provider details")

    client = ElevenLabsClient(settings=make_test_settings())
    client.client = Mock()
    client.client.text_to_speech.convert.return_value = chunks()
    with pytest.raises(ExternalServiceUnavailable, match="Speech generation"):
        client.save_audio(
            client.convert_text_to_speech("Hello"), tmp_path / "speech.mp3"
        )


@pytest.mark.parametrize("deferred", [False, True])
def test_command_errors_use_correct_response_channel(
    tmp_path: Path, deferred: bool
) -> None:
    bot = create_discord_bot(make_test_settings(data_dir=tmp_path))
    context = SimpleNamespace(
        interaction=SimpleNamespace(response=SimpleNamespace(is_done=lambda: deferred)),
        respond=AsyncMock(),
        followup=SimpleNamespace(send=AsyncMock()),
    )
    asyncio.run(
        bot.on_application_command_error(
            context,
            discord.ApplicationCommandInvokeError(
                AccessDenied("Only administrators can use this command.")
            ),
        )
    )
    sent = context.followup.send if deferred else context.respond
    sent.assert_awaited_once()
    assert sent.await_args.args == ("Only administrators can use this command.",)
    assert sent.await_args.kwargs["ephemeral"] is True
