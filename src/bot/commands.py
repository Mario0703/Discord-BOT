import asyncio
from datetime import datetime, timedelta, timezone
import os

import discord
from pathlib import Path
from bot.modules.client.openAI.askingOpenAI import AskOpenAI
from bot.modules.client.openAI.codeReview import CodeReview
from bot.modules.client.openAI.summary import SummaryOpenAI
from bot.modules.client.openAI.transcript import Transcript
from bot.modules.client.openAI.topDeals import TopDealsService

GUILD_IDS = [770744107559682108]
MAX_MESSAGE_LENGTH = 2_000
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
    """Return an inclusive date range suitable for Discord history queries."""
    start_date = datetime.fromisoformat(start)
    end_date = datetime.fromisoformat(end)

    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)

    # A date such as 2026-08-31 means the entire calendar day, not midnight only.
    if "T" not in end and " " not in end:
        end_date += timedelta(days=1)

    if end_date <= start_date:
        raise ValueError("The end date must be after the start date")

    return start_date, end_date


def register_pycord_command(
    bot: discord.Bot,
    openai_service: AskOpenAI,
    top_deals_service: TopDealsService,
    code_review_service: CodeReview,
    summary_service: SummaryOpenAI,
    transcript_service: Transcript,
) -> None:

    assistant = bot.create_group(
        "assistant",
        "AI assistant commands",
        guild_ids=GUILD_IDS,
    )

    @assistant.command(name="ask", description="Ask Luna a question")
    async def ask_openai(ctx: discord.ApplicationContext, question: str):
        await ctx.defer()
        answer = await openai_service.ask_openai(question, ctx)
        await ctx.followup.send(answer[:MAX_MESSAGE_LENGTH])

    @assistant.command(
        name="clear_conversation",
        description="Clear your Luna conversation history",
    )
    async def clear_conversation(ctx: discord.ApplicationContext):
        cleared = await openai_service.clear_conversation(ctx)

        if cleared:
            await ctx.respond("Your conversation history has been cleared.")
        else:
            await ctx.respond("You do not have any conversation history to clear.")

    @assistant.command(name="deals", description="Get the top Steam deals")
    async def deals(ctx: discord.ApplicationContext):
        await ctx.defer()
        deals_text = await top_deals_service.get_top_steam_deals()

        for start in range(0, len(deals_text), MAX_MESSAGE_LENGTH):
            await ctx.followup.send(deals_text[start : start + MAX_MESSAGE_LENGTH])

    general = bot.create_group(
        "general",
        "General bot commands",
        guild_ids=GUILD_IDS,
    )

    @general.command(name="hello", description="Say hello")
    async def hello(ctx: discord.ApplicationContext):
        await ctx.respond("Hi")

    @general.command(name="summarize", description="Summarize a channel")
    async def summarize(
        ctx: discord.ApplicationContext,
        start: str,
        end: str,
        channel_name: str,
    ):
        if ctx.guild is None:
            await ctx.respond("This command can only be used in a server.")
            return

        try:
            start_date, end_date = summary_date_range(start, end)
        except ValueError:
            await ctx.respond(
                "Use ISO dates, for example: `2026-08-31` to `2026-08-31`."
            )
            return

        selected_channel = discord.utils.get(
            ctx.guild.text_channels,
            name=channel_name.removeprefix("#"),
        )
        if selected_channel is None:
            await ctx.respond(f"I couldn't find the channel `{channel_name}`.")
            return

        await ctx.defer()
        messages = []
        async for message in selected_channel.history(
            limit=None, after=start_date, before=end_date, oldest_first=True
        ):
            messages.append(
                f"[{message.created_at.isoformat()}] {message.author}: {message.content}"
            )
            print("Content:", message.content)

        summary = await summary_service.summerice_channel_history_start_to_end(
            selected_channel.name,
            start,
            end,
            "\n".join(messages) or "No messages found.",
        )

        for position in range(0, len(summary), MAX_MESSAGE_LENGTH):
            await ctx.followup.send(
                summary[position : position + MAX_MESSAGE_LENGTH],
                allowed_mentions=discord.AllowedMentions.none(),
            )

    @general.command(
        name="reminder", description="I will remind you to check something"
    )
    async def reminder(ctx: discord.ApplicationContext, seconds: int, message: str):
        await ctx.respond(f"Okay, I’ll remind you in {seconds} seconds.")

        await asyncio.sleep(seconds)

        try:
            await ctx.author.send(f"Reminder: {message}")
        except discord.Forbidden:
            await ctx.respond(f"{ctx.author.mention}, I couldn't DM you.")

    technical = bot.create_group(
        "technical", "Tech related commands", guild_ids=GUILD_IDS
    )

    @technical.command(name="code_review", description="Review source code")
    async def code_review(
        ctx: discord.ApplicationContext,
        language: str,
        code: str,
    ):
        await ctx.defer()
        review = await code_review_service.do_code_review_with_promt(language, code)
        review = format_code_review(review)

        for start in range(0, len(review), MAX_MESSAGE_LENGTH):
            await ctx.followup.send(
                review[start : start + MAX_MESSAGE_LENGTH],
                allowed_mentions=discord.AllowedMentions.none(),
            )

    @technical.command(
        name="token_report",
        description="Get token usage for each user in the last 24 hours",
    )
    async def token_rapport(ctx: discord.ApplicationContext):
        report = openai_service.get_token_report()

        if not report:
            await ctx.respond("No token usage has been recorded in the last 24 hours.")
            return

        lines = ["Token usage in the last 24 hours:"]
        for user_id, usage in report.items():
            total = usage["input"] + usage["output"]
            lines.append(
                f"<@{user_id}> — input: {usage['input']}, "
                f"output: {usage['output']}, total: {total}"
            )

        await ctx.respond("\n".join(lines)[:MAX_MESSAGE_LENGTH])

    voice_assistant = bot.create_group(
        "voice_assistant",
        "Voice assistant commands, these can ONLY be used in a voice channel",
        guild_ids=GUILD_IDS,
    )

    @voice_assistant.command(name="join", description="Join a voice channel")
    async def join(ctx: discord.ApplicationContext):
        await ctx.defer()

        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
            await ctx.followup.send("Joined the voice channel.")
        else:
            await ctx.followup.send("You are not in a voice channel.")

    @voice_assistant.command(name="leave", description="Leave the voice channel")
    async def leave(ctx: discord.ApplicationContext):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.respond("Left the voice channel.")
        else:
            await ctx.respond("I am not in a voice channel.")

    @voice_assistant.command(
        name="upload_mp3", description="Upload an MP3 file to the voice assistant"
    )
    async def upload_mp3(ctx: discord.ApplicationContext, file: discord.Attachment):
        if not file.filename.lower().endswith(".mp3"):
            await ctx.respond("Please upload a valid MP3 file.")
            return

        await ctx.respond("File received. Uploading and creating transcript...")
        try:
            os.makedirs(VOICE_ASSISTANT_DIR, exist_ok=True)
            filename = Path(file.filename).name
            file_path = os.path.join(VOICE_ASSISTANT_DIR, filename)
            with open(file_path, "wb") as f:
                await file.save(f)

            transcript = await transcript_service.create_transcript(file_path)

            os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
            transcript_path = os.path.join(
                TRANSCRIPTS_DIR, f"{Path(filename).stem}.txt"
            )
            with open(transcript_path, "w", encoding="utf-8") as f:
                f.write(transcript)

            await ctx.followup.send(f"Transcript created and saved")
        except Exception as error:
            print(f"MP3 upload/transcription failed: {error}")
            await ctx.followup.send(
                "I could not create the transcript. Check the bot logs for details."
            )

    @bot.event
    async def on_ready():
        print(f"{bot.user} is ready and online!")
