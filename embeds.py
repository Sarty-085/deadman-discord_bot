import discord
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from config import (
    COLOR_GAME,
    COLOR_STATS,
    COLOR_DAILY,
    COLOR_WEEKLY,
    COLOR_MONTHLY,
    COLOR_HELP,
    BOT_NAME,
)

HEARTS = {
    6: "❤️❤️❤️❤️❤️❤️",
    5: "❤️❤️❤️❤️❤️",
    4: "❤️❤️❤️❤️",
    3: "❤️❤️❤️",
    2: "❤️❤️",
    1: "❤️",
    0: "💀"
}

MEDALS = ["🥇", "🥈", "🥉", "4.", "5.", "6.", "7.", "8.", "9.", "10."]

def set_cohesive_style(embed: discord.Embed, bot_user: Optional[discord.User] = None, footer_text: Optional[str] = None):
    """Applies unified branding and footer across all bot embeds."""
    icon_url = bot_user.display_avatar.url if bot_user else None
    embed.set_author(name=f"{BOT_NAME} • Hangman", icon_url=icon_url)
    default_footer = f"{BOT_NAME} • /help • Cooperative Hangman"
    embed.set_footer(text=footer_text or default_footer, icon_url=icon_url)
    embed.timestamp = datetime.now(timezone.utc)
    return embed

def create_board_embed(
    game: Dict[str, Any],
    players: List[Dict[str, Any]],
    masked_word: str,
    letters_display: str,
    bot_user: Optional[discord.User] = None
) -> discord.Embed:
    category = game.get("category", "General")
    clue = game.get("clue", "A mysterious concept.")
    difficulty = game.get("difficulty", "NORMAL")

    diff_tag = " • 🔥 HARD" if difficulty == "HARD" else (" • 🔥🔥 EXPERT" if difficulty == "EXPERT" else "")

    embed = discord.Embed(
        title="🎯 Active Hangman Puzzle",
        description="Type single letters or guess the full word in this channel!\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        color=COLOR_GAME
    )

    # 1. Clue Field
    embed.add_field(
        name="📌 Mystery Clue",
        value=f"**[{category}{diff_tag}]**\n*{clue}*",
        inline=False
    )

    # 2. Lives Field
    if not players:
        lives_value = "*(No players in this round yet. Type a letter to join!)*"
    else:
        lines = []
        for p in players:
            u_name = p.get("user_name", "Player")
            lives = p.get("lives", 0)
            hint_used = p.get("hint_used", 0)
            heart_str = HEARTS.get(lives, "💀")
            hint_str = " (🔍)" if (lives > 0 and not hint_used) else ""
            lines.append(f"**@{u_name}**: {heart_str}{hint_str}")
        lives_value = "\n".join(lines)

    embed.add_field(name="🛡️ Survivor Lives", value=lives_value, inline=False)

    # 3. Secret Word Field
    embed.add_field(name="🧩 Secret Word", value=f"`{masked_word}`", inline=False)

    # 4. Alphabet Tracker
    embed.add_field(name="🔠 Guessed Letters", value=letters_display, inline=False)

    return set_cohesive_style(embed, bot_user)

def create_profile_embed(
    member: discord.Member,
    profile: Dict[str, Any],
    server_stats: Optional[Dict[str, Any]],
    is_owner: bool = False,
    bot_user: Optional[discord.User] = None
) -> discord.Embed:
    embed = discord.Embed(
        title=f"👤 Player Profile — {member.display_name}",
        description=f"Global ranking and hangman achievements for {member.mention}.\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        color=COLOR_STATS
    )
    embed.set_thumbnail(url=member.display_avatar.url)

    badges = []
    if is_owner:
        badges.append("⚡👨‍💻 Bot Owner")
    if profile.get("badges"):
        badges.append(profile["badges"])

    badges_str = " ".join(badges) if badges else "*No badges earned yet. Reach Top 1 in Monthly to win seasonal badges!*"

    # Global Stats
    embed.add_field(name="🌐 Global Total XP", value=f"**{profile['total_xp']:,} XP**", inline=True)
    embed.add_field(name="🏆 Global Monthly XP", value=f"**{profile['monthly_xp']:,} XP**", inline=True)
    embed.add_field(name="🧩 Puzzles Solved", value=f"**{profile['words_solved']:,}**", inline=True)

    # Server specific stats
    srv_daily = server_stats["daily_xp"] if server_stats else 0
    srv_weekly = server_stats["weekly_xp"] if server_stats else 0
    srv_total = server_stats["total_xp"] if server_stats else 0

    embed.add_field(name="📅 Server Daily XP", value=f"**{srv_daily:,} XP**", inline=True)
    embed.add_field(name="📆 Server Weekly XP", value=f"**{srv_weekly:,} XP**", inline=True)
    embed.add_field(name="🏰 Server Total XP", value=f"**{srv_total:,} XP**", inline=True)

    embed.add_field(name="🎖️ Synced Badges & Honors", value=badges_str, inline=False)

    return set_cohesive_style(embed, bot_user, f"Synced across {profile.get('servers_count', 1)} active servers")

def create_leaderboard_embed(
    title: str,
    description: str,
    players: List[Dict[str, Any]],
    xp_field: str,
    color: int,
    footer_text: str,
    bot_user: Optional[discord.User] = None
) -> discord.Embed:
    embed = discord.Embed(
        title=title,
        description=f"{description}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        color=color
    )

    if not players:
        embed.add_field(name="", value="*No points recorded for this period yet! Make a guess to climb the ranks.*", inline=False)
    else:
        lines = []
        for i, p in enumerate(players):
            medal = MEDALS[i] if i < len(MEDALS) else f"`{i+1}.`"
            lines.append(f"{medal} **@{p['user_name']}** — `{p[xp_field]:,} XP`")
        embed.add_field(name="", value="\n".join(lines), inline=False)

    return set_cohesive_style(embed, bot_user, footer_text)

def create_timeout_embed(word: str, bot_user: Optional[discord.User] = None) -> discord.Embed:
    embed = discord.Embed(
        title="⏰ Word Expired (8 Hours Unsolved)",
        description=f"The mystery word remained unsolved for over **8 hours**!\n\nThe secret word was: **{word}**\n\n*Spawning a brand new challenge for the server...*",
        color=0xED4245  # Alert Red
    )
    return set_cohesive_style(embed, bot_user)
