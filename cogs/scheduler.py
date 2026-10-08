import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone
import time
from typing import Optional

from config import COLOR_DAILY, COLOR_WEEKLY, COLOR_MONTHLY
from database import (
    get_all_guild_settings,
    get_stale_active_games,
    get_server_leaderboard,
    get_global_monthly_leaderboard,
    reset_daily_xp,
    reset_weekly_xp,
    reset_monthly_xp,
    record_leaderboard_history,
    add_global_badge,
)
from embeds import (
    create_timeout_embed,
    set_cohesive_style,
)

SEASONAL_BADGES = {
    1: "🎆 New Year Champion",
    2: "💝 Valentine Champion",
    3: "🍀 Spring Equinox Champion",
    4: "🐰 Easter Blossom Champion",
    5: "🌸 Spring Bloom Champion",
    6: "☀️ Summer Solstice Champion",
    7: "🎆 Midsummer Star Champion",
    8: "🌕 Harvest Moon Champion",
    9: "🍂 Autumn Equinox Champion",
    10: "🎃 Halloween Phantom Champion",
    11: "🪔 Festival of Lights Champion",
    12: "🎄 Winter Frost Champion",
}

MEDALS = ["🥇", "🥈", "🥉", "4.", "5.", "6.", "7.", "8.", "9.", "10."]

class SchedulerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.last_checked_day: Optional[int] = None
        self.periodic_scheduler.start()

    def cog_unload(self):
        self.periodic_scheduler.cancel()

    @tasks.loop(minutes=1)
    async def periodic_scheduler(self):
        try:
            await self.bot.wait_until_ready()
        except RuntimeError:
            return
        now_utc = datetime.now(timezone.utc)

        # 1. Check for stale active games (unsolved for 8 hours)
        await self.check_stale_games()

        # 2. Check for UTC midnight reset events
        current_day = now_utc.day
        if self.last_checked_day is None:
            self.last_checked_day = current_day
            return

        if current_day != self.last_checked_day and now_utc.hour == 0:
            self.last_checked_day = current_day
            await self.execute_midnight_resets(now_utc)

    async def check_stale_games(self):
        """Automatically skips words that have remained unsolved for 8 hours (28800s)."""
        stale_games = await get_stale_active_games(max_age_seconds=8 * 3600)
        game_cog = self.bot.get_cog("GameCog")
        if not game_cog:
            return

        for game in stale_games:
            channel_id = game["channel_id"]
            channel = self.bot.get_channel(channel_id)
            if not channel:
                continue

            try:
                # Post 8-hour timeout embed
                timeout_embed = create_timeout_embed(game["word"], self.bot.user)
                await channel.send(embed=timeout_embed)

                # Automatically spawn next word
                next_embed = await game_cog.start_new_round(channel)
                await channel.send(embed=next_embed)
            except Exception as e:
                print(f"Error handling 8hr stale game in channel {channel_id}: {e}")

    async def execute_midnight_resets(self, now_utc: datetime):
        guild_settings = await get_all_guild_settings()

        # --- A. Daily Reset & Crown Hero of the Day ---
        for setting in guild_settings:
            guild_id = setting["guild_id"]
            channel_id = setting["game_channel_id"]
            guild = self.bot.get_guild(guild_id)
            if not guild:
                continue
            channel = guild.get_channel(channel_id)
            if not channel:
                continue

            top_players = await get_server_leaderboard(guild_id, period="daily", limit=1)
            if top_players and top_players[0]["daily_xp"] > 0:
                top_hero = top_players[0]
                embed = discord.Embed(
                    title="👑 Hear ye, hear ye! The Hero of the Day has been crowned!",
                    description="With an impressive score, our champion of yesterday has proven their might!\n\nDaily counters have been reset. On to a new day!\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                    color=COLOR_DAILY
                )
                embed.add_field(name="Congratulations to:", value=f"🎊 **@{top_hero['user_name']}** 🎊", inline=False)
                set_cohesive_style(embed, self.bot.user, f"Server: {guild.name}")
                try:
                    await channel.send(embed=embed)
                    await record_leaderboard_history(guild_id, "daily", top_hero["user_id"], top_hero["user_name"], top_hero["daily_xp"])
                except Exception as e:
                    print(f"Error sending Hero of the Day: {e}")

        # --- B. Weekly Reset (Sunday 00:00 UTC) ---
        if now_utc.weekday() == 6:
            for setting in guild_settings:
                guild_id = setting["guild_id"]
                channel_id = setting["game_channel_id"]
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    continue
                channel = guild.get_channel(channel_id)
                if not channel:
                    continue

                top_weekly = await get_server_leaderboard(guild_id, period="weekly", limit=10)
                if top_weekly:
                    embed = discord.Embed(
                        title="📆 Weekly Top 10 – Hangman Heroes",
                        description=f"Final weekly leaderboard results for **{guild.name}**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                        color=COLOR_WEEKLY
                    )
                    lines = []
                    for i, p in enumerate(top_weekly):
                        medal = MEDALS[i] if i < len(MEDALS) else f"`{i+1}.`"
                        lines.append(f"{medal} **@{p['user_name']}** — `{p['weekly_xp']:,} XP`")
                    embed.add_field(name="", value="\n".join(lines), inline=False)
                    set_cohesive_style(embed, self.bot.user, "Weekly counters have been reset! Good luck this week!")
                    try:
                        await channel.send(embed=embed)
                    except Exception as e:
                        print(f"Error sending weekly leaderboard: {e}")
            await reset_weekly_xp()

        # --- C. Monthly Reset & Award Top 1 Seasonal Badges (1st of month) ---
        if now_utc.day == 1:
            top_monthly = await get_global_monthly_leaderboard(limit=10)
            prev_month = 12 if now_utc.month == 1 else now_utc.month - 1
            seasonal_badge = SEASONAL_BADGES.get(prev_month, "🌟 Seasonal Champion")

            if top_monthly:
                # Top 1 receives Crown and Seasonal Badge permanently synced across all servers!
                top_champion = top_monthly[0]
                await add_global_badge(top_champion["user_id"], f"👑 {seasonal_badge}")

                # Top 2 and 3 receive Silver / Bronze badges
                if len(top_monthly) > 1:
                    await add_global_badge(top_monthly[1]["user_id"], "🥈 Monthly Silver")
                if len(top_monthly) > 2:
                    await add_global_badge(top_monthly[2]["user_id"], "🥉 Monthly Bronze")

                for setting in guild_settings:
                    channel_id = setting["game_channel_id"]
                    channel = self.bot.get_channel(channel_id)
                    if not channel:
                        continue
                    embed = discord.Embed(
                        title="🏆 MONTHLY GLOBAL CHAMPIONS 🏆",
                        description=(
                            f"The month has concluded! Congratulations to our ultimate heroes across ALL servers!\n\n"
                            f"🌟 **#1 Champion Awarded**: `{seasonal_badge}` (Synced to Profile!)\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                        ),
                        color=COLOR_MONTHLY
                    )
                    lines = []
                    for i, p in enumerate(top_monthly):
                        medal = MEDALS[i] if i < len(MEDALS) else f"`{i+1}.`"
                        lines.append(f"{medal} **@{p['user_name']}** — `{p['monthly_xp']:,} XP`")
                    embed.add_field(name="Global Podium", value="\n".join(lines), inline=False)
                    set_cohesive_style(embed, self.bot.user, f"Monthly reset complete • {len(self.bot.guilds)} servers tracked")
                    try:
                        await channel.send(embed=embed)
                    except Exception as e:
                        print(f"Error broadcasting monthly champions: {e}")
            await reset_monthly_xp()

        # Reset daily counters
        await reset_daily_xp()

async def setup(bot: commands.Bot):
    await bot.add_cog(SchedulerCog(bot))
