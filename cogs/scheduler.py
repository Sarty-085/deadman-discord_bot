import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone
import asyncio

from config import COLOR_DAILY, COLOR_WEEKLY, COLOR_MONTHLY
from database import (
    get_all_guild_settings,
    get_server_leaderboard,
    get_global_monthly_leaderboard,
    reset_daily_xp,
    reset_weekly_xp,
    reset_monthly_xp,
    record_leaderboard_history,
    add_badge_to_user,
)

MEDALS = ["🥇", "🥈", "🥉", "4.", "5.", "6.", "7.", "8.", "9.", "10."]

class SchedulerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.last_checked_day: Optional[int] = None
        self.daily_reset_task.start()

    def cog_unload(self):
        self.daily_reset_task.cancel()

    @tasks.loop(minutes=1)
    async def daily_reset_task(self):
        await self.bot.wait_until_ready()
        now_utc = datetime.now(timezone.utc)

        # Check if it is midnight UTC (minute 0 or 1) and we haven't run today yet
        current_day = now_utc.day
        if self.last_checked_day is None:
            self.last_checked_day = current_day
            return

        if current_day != self.last_checked_day and now_utc.hour == 0:
            self.last_checked_day = current_day
            await self.execute_resets(now_utc)

    async def execute_resets(self, now_utc: datetime):
        guild_settings = await get_all_guild_settings()

        # 1. Daily Reset & Crown Hero of the Day
        for setting in guild_settings:
            guild_id = setting["guild_id"]
            channel_id = setting["game_channel_id"]
            guild = self.bot.get_guild(guild_id)
            if not guild:
                continue
            channel = guild.get_channel(channel_id)
            if not channel:
                continue

            # Top daily player
            top_players = await get_server_leaderboard(guild_id, period="daily", limit=1)
            if top_players and top_players[0]["daily_xp"] > 0:
                top_hero = top_players[0]
                embed = discord.Embed(
                    title="👑 Hear ye, hear ye! The Hero of the Day has been crowned!",
                    description="With an impressive score, our champions of yesterday have proven their might!\n\nDaily counters have been reset. On to a new day!",
                    color=COLOR_DAILY
                )
                embed.set_footer(text=f"Server: {guild.name}")
                embed.add_field(name="Congratulations to:", value=f"🎊@{top_hero['user_name']}🎊", inline=False)
                try:
                    await channel.send(embed=embed)
                    await record_leaderboard_history(guild_id, "daily", top_hero["user_id"], top_hero["user_name"], top_hero["daily_xp"])
                except Exception as e:
                    print(f"Error sending Hero of the Day in guild {guild_id}: {e}")

        # 2. Weekly Reset (Every Sunday midnight UTC)
        # In Python weekday(): Monday is 0, Sunday is 6
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
                        description=f"Weekly leaderboard for **{guild.name}**",
                        color=COLOR_WEEKLY
                    )
                    lines = []
                    for i, p in enumerate(top_weekly):
                        medal = MEDALS[i] if i < len(MEDALS) else f"{i+1}."
                        lines.append(f"{medal} @{p['user_name']} — **{p['weekly_xp']} XP**")
                    embed.add_field(name="", value="\n".join(lines), inline=False)
                    try:
                        await channel.send(embed=embed)
                    except Exception as e:
                        print(f"Error sending weekly leaderboard in guild {guild_id}: {e}")
            await reset_weekly_xp()

        # 3. Monthly Reset (1st day of month)
        if now_utc.day == 1:
            top_monthly = await get_global_monthly_leaderboard(limit=10)
            if top_monthly:
                # Crown top 3 monthly with Champion badge
                for p in top_monthly[:3]:
                    await add_badge_to_user(p["user_id"], "👑")

                for setting in guild_settings:
                    channel_id = setting["game_channel_id"]
                    channel = self.bot.get_channel(channel_id)
                    if not channel:
                        continue
                    embed = discord.Embed(
                        title="🏆 MONTHLY GLOBAL CHAMPIONS 🏆",
                        description="The ultimate heroes across ALL servers!\n\nCongratulations to our top performers this month!",
                        color=COLOR_MONTHLY
                    )
                    embed.set_footer(text=f"Monthly counters have been reset! | Servers tracked: {len(self.bot.guilds)}")
                    lines = []
                    for i, p in enumerate(top_monthly):
                        medal = MEDALS[i] if i < len(MEDALS) else f"{i+1}."
                        lines.append(f"{medal} @{p['user_name']} — **{p['monthly_xp']} XP**")
                    embed.add_field(name="", value="\n".join(lines), inline=False)
                    try:
                        await channel.send(embed=embed)
                    except Exception as e:
                        print(f"Error sending monthly champions: {e}")
            await reset_monthly_xp()

        # Reset daily counters
        await reset_daily_xp()

async def setup(bot: commands.Bot):
    await bot.add_cog(SchedulerCog(bot))
