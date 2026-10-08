import asyncio
import logging
import os
import sys

import discord
from discord.ext import commands

from config import BOT_NAME, BOT_PREFIX, DISCORD_TOKEN
from database import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("WholesomeBot")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(
    command_prefix=BOT_PREFIX,
    intents=intents,
    help_command=None  # We use custom h!help embed in StatsCog
)

INITIAL_EXTENSIONS = [
    "cogs.game",
    "cogs.admin",
    "cogs.stats",
    "cogs.scheduler",
]

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    logger.info(f"Loaded on {len(bot.guilds)} servers")
    activity = discord.Game(name=f"Hangman | {BOT_PREFIX}help")
    await bot.change_presence(activity=activity)
    logger.info(f"{BOT_NAME} is ready to play!")

async def main():
    logger.info("Initializing database...")
    await init_db()

    for extension in INITIAL_EXTENSIONS:
        try:
            await bot.load_extension(extension)
            logger.info(f"Loaded extension: {extension}")
        except Exception as e:
            logger.error(f"Failed to load extension {extension}: {e}")

    if not DISCORD_TOKEN:
        logger.error("No DISCORD_TOKEN found! Please set DISCORD_TOKEN in your .env file or hosting environment variables.")
        return

    logger.info("Starting bot...")
    await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
