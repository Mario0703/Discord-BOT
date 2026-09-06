from bot.main import create_discord_bot
from bot.Settings.settings import load_settings


def run_bot():
    settings = load_settings()
    create_discord_bot(settings).run(settings.discord_token)


if __name__ == "__main__":
    run_bot()
