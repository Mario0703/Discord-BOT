# Discord AI Bot

A Python 3.10+ Discord bot built with Pycord, OpenAI, and ElevenLabs. It answers
questions, reviews code, summarizes channel history, finds game deals and weather,
and transcribes or reads audio aloud.

## Features and examples

| Command | Example / behavior |
| --- | --- |
| `/assistant ask` | `question: What is the weather in Copenhagen, DK?` — conversational answers with weather and game-deal tools. |
| `/assistant clear_conversation` | Delete your active assistant conversation and its local reference. |
| `/assistant deals` | Fetch and rank three Steam deals for Denmark. The current preset uses an 80% discount filter. |
| `/assistant model` | List supported models available to the configured OpenAI account. |
| `/assistant select_model` | Save a `model_id` and `reasoning_level` from that list. |
| `/assistant show_my_model` | Show your saved selection or the configured default. |
| `/technical code_review` | `language: python`, `code: def add(a, b): return a + b` — request a review without adding it to assistant history. |
| `/technical token_report` | Administrator-only input/output token totals per user for the last 24 hours. |
| `/general summarize` | `start: 2026-08-30`, `end: 2026-08-31`, `channel_name: general` — summarize accessible channel history. |
| `/general reminder` | `seconds: 60`, `message: Check the build` — send a reminder by DM. |
| `/general hello`, `/help` | Greet the bot or list registered commands. |
| `/voice_assistant upload_mp3` | Attach an MP3 to transcribe and save it. |
| `/voice_assistant list_transcripts`, `/voice_assistant get_transcript` | List your saved transcripts or receive one by DM. |
| `/voice_assistant join`, `/voice_assistant leave` | Connect or disconnect the bot from voice. |
| `/voice_assistant eleven_labs`, `/voice_assistant play_transcript` | Speak supplied text or a saved transcript in your voice channel. |

## Tests and code quality

```bash
python -m pytest
python -m ruff check .
python -m black --check .
python -m mypy src
```

Use `python -m ruff check . --fix` and `python -m black .` to apply supported
lint fixes and formatting. Mypy checks every application module, rejecting
untyped definitions/calls, bare generics, and accidental `Any` returns. One
documented suppression covers Pycord's unannotated `Bot` constructor.
