from bot.Settings.settings import Settings


def make_test_settings() -> Settings:
    return Settings(
        discord_token="test-token",
        guild_ids=(123,),
        openai_api_key="test-openai-key",
    )
