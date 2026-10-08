import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("BOT_TOKEN", "")
BOT_PREFIX = os.getenv("BOT_PREFIX", "h!")
BOT_OWNER_ID = int(os.getenv("BOT_OWNER_ID")) if os.getenv("BOT_OWNER_ID") else None

BOT_NAME = "Wholesome Bot"

COLOR_GAME = 0x4169E1       # RoyalBlue
COLOR_HELP = 0x3498DB       # Blue
COLOR_STATS = 0x3498DB      # Blue
COLOR_DAILY = 0xFFD700      # Gold
COLOR_WEEKLY = 0xFFD700     # Gold
COLOR_MONTHLY = 0xFF4500    # OrangeRed
