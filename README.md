# Discord-BOT

A Discord bot built with Pycord, the OpenAI SDK, and ElevenLabs.

## Setup

Create and activate a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install runtime and development dependencies:

```powershell
python -m pip install -r requirements-dev.txt
```

Create a `.env` file with the credentials required by the bot, then start it with:

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

