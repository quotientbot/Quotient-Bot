from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from core import Quotient

import re
from contextlib import suppress

import config
import discord

from constants import random_greeting
from core import Cog, Context
from models import Guild


class MainEvents(Cog, name="Main Events"):
    def __init__(self, bot: Quotient) -> None:
        self.bot = bot

    # incomplete?, I know
    @Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        with suppress(AttributeError):
            g, b = await Guild.get_or_create(guild_id=guild.id)
            self.bot.cache.guild_data[guild.id] = {
                "prefix": g.prefix,
                "color": g.embed_color or self.bot.color,
                "footer": g.embed_footer or config.FOOTER,
            }
            self.bot.loop.create_task(guild.chunk())

    @Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or message.guild is None:
            return
        if re.match(f"^<@!?{self.bot.user.id}>$", message.content):
            ctx: Context = await self.bot.get_context(message)
            self.bot.dispatch("mention", ctx)

    @Cog.listener()
    async def on_mention(self, ctx: Context) -> None:
        prefix: str = self.bot.cache.guild_data[ctx.guild.id].get("prefix", "q")
        await ctx.send(
            f"{random_greeting()} You seem lost. Are you?\n"
            f"Current prefix for this server is: `{prefix}`.\n\nUse it like: `{prefix}help`"
        )
