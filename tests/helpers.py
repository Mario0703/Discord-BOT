from bot.settings.settings import Settings


def make_test_settings(**overrides) -> Settings:
    values = {
        "discord_token": "test-token",
        "guild_ids": (123,),
        "openai_api_key": "test-openai-key",
    }
    values.update(overrides)
    return Settings(**values)
