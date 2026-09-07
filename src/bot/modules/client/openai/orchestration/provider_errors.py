"""Translate SDK errors without exposing request data or credentials."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from openai import APIError, BadRequestError, NotFoundError

from bot.errors import ExternalServiceUnavailable, InvalidInput, ResourceNotFound


@asynccontextmanager
async def openai_errors(
    *, allow_conversation_recovery: bool = False
) -> AsyncIterator[None]:
    try:
        yield
    except (BadRequestError, NotFoundError) as error:
        if allow_conversation_recovery:
            raise
        if isinstance(error, NotFoundError):
            raise ResourceNotFound(
                "The requested OpenAI resource was not found."
            ) from error
        raise InvalidInput(
            "OpenAI could not accept this request. Check the input and model settings."
        ) from error
    except APIError as error:
        logging.getLogger(__name__).warning(
            "OpenAI request failed (%s)", type(error).__name__
        )
        raise ExternalServiceUnavailable(
            "OpenAI is temporarily unavailable. Please try again later."
        ) from error
