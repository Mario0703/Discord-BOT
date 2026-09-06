from types import SimpleNamespace

from bot.command_categories.technical import _is_administrator
from bot.command_categories.voice_assistant import (
    _transcript_path,
    _tts_text_error,
    _upload_size_error,
    _user_data_dir,
)
from tests.helpers import make_test_settings


def test_user_data_dir_is_scoped_to_guild_and_user(tmp_path):
    context = SimpleNamespace(
        guild=SimpleNamespace(id=123),
        author=SimpleNamespace(id=456),
    )

    assert _user_data_dir(tmp_path, context) == (
        tmp_path / "guilds" / "123" / "users" / "456"
    )


def test_transcript_path_cannot_escape_user_directory(tmp_path):
    path = _transcript_path(tmp_path, "../other-user/transcript.txt")

    assert path == tmp_path / "transcript.txt"
    assert path.parent == tmp_path


def test_voice_limits_are_configured():
    settings = make_test_settings()

    assert settings.upload_max_bytes == 10 * 1024 * 1024
    assert settings.tts_max_characters == 5_000


def test_custom_upload_limit_is_enforced():
    settings = make_test_settings(upload_max_bytes=100)

    assert _upload_size_error(100, settings) is None
    assert "configured size limit" in _upload_size_error(101, settings)


def test_custom_tts_limit_is_enforced():
    settings = make_test_settings(tts_max_characters=5)

    assert _tts_text_error("12345", settings) is None
    assert _tts_text_error("123456", settings) == (
        "The text cannot exceed 5 characters."
    )


def test_only_administrators_can_use_admin_commands():
    administrator = SimpleNamespace(
        guild=SimpleNamespace(id=123),
        author=SimpleNamespace(guild_permissions=SimpleNamespace(administrator=True)),
    )
    member = SimpleNamespace(
        guild=SimpleNamespace(id=123),
        author=SimpleNamespace(guild_permissions=SimpleNamespace(administrator=False)),
    )

    assert _is_administrator(administrator)
    assert not _is_administrator(member)
