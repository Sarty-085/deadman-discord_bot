import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("BOT_TOKEN", "")
BOT_PREFIX = os.getenv("BOT_PREFIX", "h!")
BOT_OWNER_ID = int(os.getenv("BOT_OWNER_ID")) if os.getenv("BOT_OWNER_ID") else None

BOT_NAME = "Wholesome Bot"

# Lavalink Server Configuration (for music hosting)
LAVALINK_HOST = os.getenv("LAVALINK_HOST", "localhost")
LAVALINK_PORT = int(os.getenv("LAVALINK_PORT", "2333"))
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD", "youshallnotpass")
LAVALINK_SECURE = os.getenv("LAVALINK_SECURE", "false").lower() in ("true", "1", "yes")

# Construct Lavalink URI for Wavelink 3.x
LAVALINK_URI = os.getenv(
    "LAVALINK_URI",
    f"{'https' if LAVALINK_SECURE else 'http'}://{LAVALINK_HOST}:{LAVALINK_PORT}"
)

# Cohesive Color Palette
COLOR_GAME = 0x5865F2       # Discord Blurple
COLOR_HELP = 0x5865F2       # Discord Blurple
COLOR_STATS = 0x5865F2      # Discord Blurple
COLOR_MUSIC = 0x5865F2      # Discord Blurple
COLOR_DAILY = 0xFEE75C      # Warm Gold
COLOR_WEEKLY = 0xFEE75C     # Warm Gold
COLOR_MONTHLY = 0xEB459E    # Fuchsia / Seasonal Champion
COLOR_TIMEOUT = 0xED4245    # Red
