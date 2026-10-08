import asyncio
import logging
import os
import sys

import discord
from discord.ext import commands

from config import BOT_NAME, BOT_PREFIX, DISCORD_TOKEN
from database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("WholesomeBot")

INITIAL_EXTENSIONS = [
    "cogs.game",
    "cogs.admin",
    "cogs.stats",
    "cogs.scheduler",
    "cogs.music",
]

class WholesomeBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.voice_states = True

        super().__init__(
            command_prefix=BOT_PREFIX,
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        logger.info("Initializing database...")
        await init_db()

        for extension in INITIAL_EXTENSIONS:
            try:
                await self.load_extension(extension)
                logger.info(f"Loaded extension: {extension}")
            except Exception as e:
                logger.error(f"Failed to load extension {extension}: {e}")

        logger.info("Syncing slash commands with Discord...")
        try:
            synced = await self.tree.sync()
            logger.info(f"Successfully synced {len(synced)} slash commands across Discord!")
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Serving across {len(self.guilds)} servers")
        activity = discord.Game(name=f"Hangman & Music | /help • {BOT_PREFIX}help")
        await self.change_presence(activity=activity)
        logger.info(f"{BOT_NAME} is fully online and ready!")

bot = WholesomeBot()

async def main():
    if not DISCORD_TOKEN:
        logger.error("No DISCORD_TOKEN found! Please set DISCORD_TOKEN in your .env file or hosting environment variables.")
        return

    logger.info("Connecting to Discord...")
    await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
