import logging

from bot.main import create_discord_bot
from bot.settings.settings import _check_api_keys_settings, load_settings


def run_bot() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    logging.captureWarnings(True)
    settings = load_settings()
    _check_api_keys_settings(settings)
    create_discord_bot(settings).run(settings.discord_token)


if __name__ == "__main__":
    run_bot()
