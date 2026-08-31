import os

from dotenv import load_dotenv

from bot.main import create_bot


def run_bot():
    load_dotenv()
    token = os.getenv("TOKEN")
    if not token:
        raise RuntimeError("Missing required environment variable: TOKEN")

    create_bot().run(token)


if __name__ == "__main__":
    run_bot()
