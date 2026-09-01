from __future__ import annotations
import discord


class User:
    """Application-level user information extracted from a Pycord context."""

    def __init__(self, ctx: discord.ApplicationContext):
        self.discord_id = str(ctx.author.id)

    def get_discord_id(self) -> str:
        return self.discord_id
    
