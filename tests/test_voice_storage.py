from types import SimpleNamespace

from bot.command_categories.technical import _is_administrator
from bot.command_categories.voice_assistant import (
    MAX_TTS_TEXT_LENGTH,
    MAX_UPLOAD_SIZE,
    _transcript_path,
    _user_data_dir,
)


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
    assert MAX_UPLOAD_SIZE == 10 * 1024 * 1024
    assert MAX_TTS_TEXT_LENGTH == 5_000


def test_only_administrators_can_use_admin_commands():
    administrator = SimpleNamespace(
        guild=SimpleNamespace(id=123),
        author=SimpleNamespace(
            guild_permissions=SimpleNamespace(administrator=True)
        ),
    )
    member = SimpleNamespace(
        guild=SimpleNamespace(id=123),
        author=SimpleNamespace(
            guild_permissions=SimpleNamespace(administrator=False)
        ),
    )

    assert _is_administrator(administrator)
    assert not _is_administrator(member)
