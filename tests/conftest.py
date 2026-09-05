"""Shared pytest configuration."""

from __future__ import annotations

import getpass
import os
from pathlib import Path

import pytest


def _account_name() -> str:
    """Return the real process account instead of an inherited USERNAME value."""
    try:
        name = os.getlogin()
    except OSError:
        name = getpass.getuser()

    return "".join(
        character if character.isalnum() or character in "-_." else "_"
        for character in name
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """Keep pytest temp roots separate for each Windows process account."""
    if config.option.basetemp is None:
        temp_directory = f".pytest-tmp-{_account_name()}"
        config.option.basetemp = Path(config.rootpath) / temp_directory
