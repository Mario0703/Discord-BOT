# Discord-BOT

This project is a Discord bot built with Pycord that integrates the OpenAI and ElevenLabs SDKs. Its goal is to explore how large language models and AI-generated audio can be integrated into a Discord application, including features such as conversational responses, code reviews, and voice-related functionality.

## Setup

Create and activate a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install runtime and development dependencies:

```powershell
pip install -e ".[dev]"
```

The `.env.example` file lists the environment variables required to run the bot, including the Discord bot token and API keys for OpenAI, ElevenLabs, and other services. Users should copy this file to .env and fill in their own credentials.

Finally, to run the bot, use:

```powershell
python -m bot
```


## Code quality

Run linting, formatting checks, type checking, and tests:

```powershell
python -m ruff check .
python -m black --check .
python -m mypy src
python -m pytest
```

Ruff can automatically fix supported lint issues:

```powershell
python -m ruff check . --fix
```

To format the project with Black:

```powershell
python -m black .
```
