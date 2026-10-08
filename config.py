import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("BOT_TOKEN", "")
BOT_PREFIX = os.getenv("BOT_PREFIX", "h!")
BOT_OWNER_ID = int(os.getenv("BOT_OWNER_ID")) if os.getenv("BOT_OWNER_ID") else None

BOT_NAME = "Wholesome Bot"

# Cohesive Color Palette
COLOR_GAME = 0x5865F2       # Discord Blurple
COLOR_HELP = 0x5865F2       # Discord Blurple
COLOR_STATS = 0x5865F2      # Discord Blurple
COLOR_DAILY = 0xFEE75C      # Warm Gold
COLOR_WEEKLY = 0xFEE75C     # Warm Gold
COLOR_MONTHLY = 0xEB459E    # Fuchsia / Seasonal Champion
COLOR_TIMEOUT = 0xED4245    # Red
