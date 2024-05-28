import logging
import os
from datetime import datetime

import aiohttp
import discord
from asyncpg import Pool
from discord.ext import commands
from tortoise import Tortoise, timezone

__all__ = ("Quotient",)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"


log = logging.getLogger(os.getenv("INSTANCE_TYPE"))


class Quotient(commands.AutoShardedBot):
    session: aiohttp.ClientSession

    def __init__(self):
        super().__init__(
            command_prefix=os.getenv("DEFAULT_PREFIX"),
            enable_debug_events=True,
            intents=intents,
            strip_after_prefix=True,
            case_insensitive=True,
            allowed_mentions=discord.AllowedMentions(
                everyone=False, roles=False, replied_user=True, users=True
            ),
        )

        self.seen_messages: int = 0

    async def setup_hook(self) -> None:
        self.session = aiohttp.ClientSession()

        await Tortoise.init(
            config={
                "use_tz": True,
                "timezone": "Asia/Kolkata",
                "connections": {
                    "quotient": {
                        "engine": "tortoise.backends.asyncpg",
                        "credentials": {
                            "database": os.getenv("QUOTIENT_DB_NAME"),
                            "host": os.getenv("QUOTIENT_DB_HOST"),
                            "password": os.getenv("QUOTIENT_DB_PASSWORD"),
                            "port": 5432,
                            "user": os.getenv("QUOTIENT_DB_USER"),
                        },
                    },
                    "pro": {
                        "engine": "tortoise.backends.asyncpg",
                        "credentials": {
                            "database": os.getenv("PRO_DB_NAME"),
                            "host": os.getenv("PRO_DB_HOST"),
                            "password": os.getenv("PRO_DB_PASSWORD"),
                            "port": 5432,
                            "user": os.getenv("PRO_DB_USER"),
                        },
                    },
                },
                "apps": {
                    "default": {
                        "models": ["models"],
                        "default_connection": os.getenv("INSTANCE_TYPE"),
                    },
                },
            }
        )
        log.info("Tortoise has been initialized.")
        await Tortoise.generate_schemas(safe=True)

        for model_name, model in Tortoise.apps.get("default").items():
            model.bot = self

        for extension in os.getenv("EXTENSIONS").split(","):
            try:
                await self.load_extension(extension)
            except Exception as _:
                log.exception("Failed to load extension %s.", extension)

    @property
    def current_time(self) -> datetime:
        return timezone.now()

    @property
    def my_pool(self) -> Pool:

        return Tortoise.get_connection(os.getenv("INSTANCE_TYPE"))._pool

    @property
    def quotient_pool(self) -> Pool:
        return Tortoise.get_connection("quotient")._pool

    @property
    def pro_pool(self) -> Pool:
        return Tortoise.get_connection("pro")._pool

    @property
    async def on_message(self, message: discord.Message) -> None:
        self.seen_messages += 1

        if message.guild is None or message.author.bot:
            return

        await self.process_commands(message)

    async def on_ready(self) -> None:
        log.info("Ready: %s (ID: %s)", self.user, self.user.id)

    async def on_shard_resumed(self, shard_id: int) -> None:
        log.info("Shard ID %s has resumed...", shard_id)

    async def start(self) -> None:
        await super().start(os.getenv("DISCORD_TOKEN"), reconnect=True)

    async def close(self) -> None:
        await super().close()

        if hasattr(self, "session"):
            await self.session.close()

        log.info(f"{self.user} has logged out.")

        await Tortoise.close_connections()
        log.info("Tortoise connections have been closed.")
