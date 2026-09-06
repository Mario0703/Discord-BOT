from bot.main import create_discord_bot
from bot.Settings.settings import _check_api_keys_settings, load_settings


def run_bot():
    settings = load_settings()
    _check_api_keys_settings(settings)
    create_discord_bot(settings).run(settings.discord_token)


if __name__ == "__main__":
    run_bot()
