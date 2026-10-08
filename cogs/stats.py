import discord
from discord.ext import commands
from typing import Optional

from config import (
    COLOR_HELP,
    COLOR_STATS,
    COLOR_DAILY,
    COLOR_WEEKLY,
    COLOR_MONTHLY,
    BOT_OWNER_ID,
)
from database import (
    get_user_stats,
    get_server_leaderboard,
    get_global_monthly_leaderboard,
    get_server_stats,
)

MEDALS = ["🥇", "🥈", "🥉", "4.", "5.", "6.", "7.", "8.", "9.", "10."]

class StatsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_cmd(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🎮 Hangman Bot Commands",
            description="All available commands for the Hangman bot",
            color=COLOR_HELP
        )
        embed.set_footer(text="Prefix: h! | Top 3 monthly players become Champions!")

        embed.add_field(
            name="🎯 Game Commands (Everyone)",
            value="`h!start` - Start a new hangman game\n`h!hint` - Get a hint (reveals 1 letter, once per word)",
            inline=False
        )
        embed.add_field(
            name="📊 Stats Commands (Everyone)",
            value=(
                "`h!stats` - View your personal stats\n"
                "`h!daily` - View your daily stats & leaderboard\n"
                "`h!weekly` - View weekly server leaderboard\n"
                "`h!monthly` - View monthly global leaderboard\n"
                "`h!serverstats` - View server statistics\n"
                "`h!leaderboard` / `h!lb` / `h!top` - Quick leaderboard"
            ),
            inline=False
        )
        embed.add_field(
            name="🛡️ Admin Commands",
            value="`h!setchannel` - Set current channel as game channel\n`h!skip` - Skip current word (requires Manage Messages)",
            inline=False
        )
        embed.add_field(
            name="💡 How to Play",
            value="Simply type a letter or full word in the game channel to play!\nGuess correctly to earn XP. Watch out for your lives!",
            inline=False
        )
        embed.add_field(
            name="🏆 Badges & Ribbons",
            value=(
                "👑 = Current Monthly Champion\n"
                "⚡👨‍💻 = Bot Owner\n"
                "🥉 = 1 Title | 🥈 = 3 Titles | 🥇 = 6 Titles | 🏅 = 12 Titles\n"
                "🎃🎄🌕🪔🎆💝🐰 = Seasonal Event Badges"
            ),
            inline=False
        )

        await ctx.send(embed=embed)

    @commands.command(name="stats")
    async def stats(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        target = member or ctx.author
        stats = await get_user_stats(target.id, ctx.guild.id)

        embed = discord.Embed(
            title=f"📊 Hangman Stats — {target.display_name}",
            color=COLOR_STATS
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        badges = []
        if target.id == BOT_OWNER_ID:
            badges.append("⚡👨‍💻 Bot Owner")
        if stats and stats.get("badges"):
            badges.append(stats["badges"])

        badges_str = " ".join(badges) if badges else "None yet"

        total_xp = stats["total_xp"] if stats else 0
        daily_xp = stats["daily_xp"] if stats else 0
        weekly_xp = stats["weekly_xp"] if stats else 0
        monthly_xp = stats["monthly_xp"] if stats else 0
        solved = stats["words_solved"] if stats else 0

        embed.add_field(name="⭐ Total XP", value=f"**{total_xp:,} XP**", inline=True)
        embed.add_field(name="📅 Daily XP", value=f"**{daily_xp:,} XP**", inline=True)
        embed.add_field(name="📆 Weekly XP", value=f"**{weekly_xp:,} XP**", inline=True)
        embed.add_field(name="🏆 Monthly XP", value=f"**{monthly_xp:,} XP**", inline=True)
        embed.add_field(name="🧩 Words Cracked", value=f"**{solved:,}**", inline=True)
        embed.add_field(name="🎖️ Badges", value=badges_str, inline=True)

        await ctx.send(embed=embed)

    @commands.command(name="daily")
    async def daily(self, ctx: commands.Context):
        top_players = await get_server_leaderboard(ctx.guild.id, period="daily", limit=10)

        embed = discord.Embed(
            title="📅 Today's Leaderboard",
            description=f"Top players today in **{ctx.guild.name}**",
            color=COLOR_DAILY
        )
        embed.set_footer(text="Daily stats reset every midnight UTC")

        if not top_players:
            embed.add_field(name="", value="No points scored today yet! Be the first to guess!", inline=False)
        else:
            lines = []
            for i, p in enumerate(top_players):
                medal = MEDALS[i] if i < len(MEDALS) else f"{i+1}."
                lines.append(f"{medal} @{p['user_name']} — **{p['daily_xp']} XP**")
            embed.add_field(name="", value="\n".join(lines), inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="weekly")
    async def weekly(self, ctx: commands.Context):
        top_players = await get_server_leaderboard(ctx.guild.id, period="weekly", limit=10)

        embed = discord.Embed(
            title="📆 Weekly Leaderboard",
            description=f"Top players this week in **{ctx.guild.name}**",
            color=COLOR_WEEKLY
        )
        embed.set_footer(text="Weekly leaderboard resets every Sunday at midnight UTC")

        if not top_players:
            embed.add_field(name="", value="No points scored this week yet! Start playing to climb the ranks!", inline=False)
        else:
            lines = []
            for i, p in enumerate(top_players):
                medal = MEDALS[i] if i < len(MEDALS) else f"{i+1}."
                lines.append(f"{medal} @{p['user_name']} — **{p['weekly_xp']} XP**")
            embed.add_field(name="", value="\n".join(lines), inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="monthly")
    async def monthly(self, ctx: commands.Context):
        top_players = await get_global_monthly_leaderboard(limit=10)
        server_count = len(self.bot.guilds)

        embed = discord.Embed(
            title="🏆 Monthly Global Leaderboard",
            description="Top players across ALL servers this month!",
            color=COLOR_MONTHLY
        )
        embed.set_footer(text=f"Resets on 1st of each month | {server_count} servers tracked")

        if not top_players:
            embed.add_field(name="", value="No players tracked this month yet!", inline=False)
        else:
            lines = []
            for i, p in enumerate(top_players):
                medal = MEDALS[i] if i < len(MEDALS) else f"{i+1}."
                lines.append(f"{medal} @{p['user_name']} — **{p['monthly_xp']} XP**")
            embed.add_field(name="", value="\n".join(lines), inline=False)

        await ctx.send(embed=embed)

    @commands.command(aliases=["lb", "top"])
    async def leaderboard(self, ctx: commands.Context):
        # Default leaderboard points to weekly
        await self.weekly(ctx)

    @commands.command(name="serverstats")
    async def serverstats(self, ctx: commands.Context):
        stats = await get_server_stats(ctx.guild.id)

        embed = discord.Embed(
            title=f"📈 Server Statistics — {ctx.guild.name}",
            color=COLOR_STATS
        )
        embed.add_field(name="👥 Active Players", value=f"**{stats['player_count']}**", inline=True)
        embed.add_field(name="🧩 Words Cracked", value=f"**{stats['words_solved']}**", inline=True)
        embed.add_field(name="⭐ Total XP Earned", value=f"**{stats['total_xp']:,} XP**", inline=True)

        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(StatsCog(bot))
