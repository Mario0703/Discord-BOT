from datetime import datetime, timedelta, timezone

import discord

from bot.command_categories.assistant import register as register_assistant
from bot.command_categories.general import register as register_general
from bot.command_categories.technical import register as register_technical
from bot.command_categories.voice_assistant import register as register_voice

GUILD_IDS = [770744107559682108]
VOICE_ASSISTANT_DIR = (
    r"F:\Python Projects\Discord Bot\Discord-BOT\src\voice channel recordings"
)
TRANSCRIPTS_DIR = r"F:\Python Projects\Discord Bot\Discord-BOT\src\bot\transcripts"


def format_code_review(review: str) -> str:
    review = review.replace("\\r\\n", "\n").replace("\\n", "\n")
    review = review.replace("```python ", "```python\n")
    review = review.replace("```py ", "```py\n")
    return review.strip()


def summary_date_range(start: str, end: str) -> tuple[datetime, datetime]:
    start_date = datetime.fromisoformat(start)
    end_date = datetime.fromisoformat(end)
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)
    if "T" not in end and " " not in end:
        end_date += timedelta(days=1)
    if end_date <= start_date:
        raise ValueError("The end date must be after the start date")
    return start_date, end_date


def register_pycord_command(
    bot: discord.Bot,
    openai_service,
    top_deals_service,
    code_review_service,
    summary_service,
    transcript_service,
    elevenlabs_service,
):

    register_assistant(bot, openai_service, top_deals_service, GUILD_IDS)
    register_general(bot, summary_service, GUILD_IDS, summary_date_range)
    register_technical(
        bot, openai_service, code_review_service, GUILD_IDS, format_code_review
    )
    register_voice(
        bot,
        transcript_service,
        elevenlabs_service,
        VOICE_ASSISTANT_DIR,
        TRANSCRIPTS_DIR,
        GUILD_IDS,
    )

    @bot.slash_command(name="help", description="Show all available bot commands", guild_ids=GUILD_IDS)
    async def help_command(ctx: discord.ApplicationContext):
        commands_by_category: dict[str, list[str]] = {}
        examples = {
            "assistant ask": "/assistant ask question: Explain async Python",
            "assistant clear_conversation": "/assistant clear_conversation",
            "assistant deals": "/assistant deals",
            "assistant model": "/assistant model",
            "assistant select_model": (
                "/assistant select_model model_id: gpt-5.6-sol "
                "reasoning_level: high"
            ),
            "assistant show_my_model": "/assistant show_my_model",
            "general hello": "/general hello",
            "general summarize": (
                "/general summarize start: 2026-09-01 end: 2026-09-02 "
                "channel_name: general"
            ),
            "technical code_review": (
                "/technical code_review language: python code: print('hello')"
            ),
            "voice_assistant upload_mp3": (
                "/voice_assistant upload_mp3 file: audio.mp3 name: meeting"
            ),
            "voice_assistant get_transcript": (
                "/voice_assistant get_transcript name: meeting"
            ),
        }

        for command in bot.walk_application_commands():
            if isinstance(command, discord.SlashCommandGroup):
                continue

            qualified_name = command.qualified_name
            category = qualified_name.split()[0].replace("_", " ").title()
            usage = f"/{qualified_name}"

            for option in command.options:
                marker = "<...>" if option.required else "[...]"
                usage += f" {option.name}{marker}"

            command_text = f"`{usage}` — {command.description}"
            example = examples.get(qualified_name)
            if example:
                command_text += f"\n  Example: `{example}`"

            commands_by_category.setdefault(category, []).append(command_text)

        help_lines = [
            "**Available bot commands**",
            "Required parameters are shown as `<...>`; optional parameters as `[...]`.",
            "",
        ]

        for category, command_lines in sorted(commands_by_category.items()):
            help_lines.append(f"**{category}**")
            help_lines.extend(command_lines)
            help_lines.append("")

        help_lines.extend(
            [
                "**Transcript workflow**",
                "1. Join a voice channel.",
                (
                    "2. Use `/voice_assistant upload_mp3` to upload an MP3 "
                    "and choose a name."
                ),
                "3. Use `/voice_assistant get_transcript` to download the transcript.",
                (
                    "4. Use `/voice_assistant play_transcript` to have the bot "
                    "read it aloud."
                ),
            ]
        )

        help_text = "\n".join(help_lines)
        chunks = _split_message(help_text)
        await ctx.respond(chunks[0])

        for chunk in chunks[1:]:
            await ctx.followup.send(chunk)

    @bot.event
    async def on_ready():
        print(f"{bot.user} is ready and online!")


def _split_message(text: str, limit: int = 2000) -> list[str]:
    chunks = []
    current_lines = []
    current_length = 0

    for line in text.splitlines():
        if len(line) > limit:
            if current_lines:
                chunks.append("\n".join(current_lines))
                current_lines = []
                current_length = 0

            for position in range(0, len(line), limit):
                chunks.append(line[position : position + limit])
            continue

        line_length = len(line) + (1 if current_lines else 0)
        if current_lines and current_length + line_length > limit:
            chunks.append("\n".join(current_lines))
            current_lines = []
            current_length = 0

        current_lines.append(line)
        current_length += len(line) + (1 if len(current_lines) > 1 else 0)

    if current_lines:
        chunks.append("\n".join(current_lines))

    return chunks or [""]
