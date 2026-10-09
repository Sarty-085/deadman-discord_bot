import discord
from discord.ext import commands
from typing import Optional

from config import (
    COLOR_HELP,
    COLOR_DAILY,
    COLOR_WEEKLY,
    COLOR_MONTHLY,
    COLOR_STATS,
    BOT_OWNER_ID,
)
from database import (
    get_user_stats,
    get_global_user_profile,
    get_server_leaderboard,
    get_global_monthly_leaderboard,
    get_server_stats,
)
from embeds import (
    create_profile_embed,
    create_leaderboard_embed,
    set_cohesive_style,
)

class StatsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="help",
        description=f"View the {BOT_NAME} hangman rules, commands, and badge guide."
    )
    async def help_cmd(self, ctx: commands.Context):
        embed = discord.Embed(
            title=f"🎮 {BOT_NAME} — Hangman Guide",
            description="Welcome to cooperative multiplayer Hangman with clues!\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            color=COLOR_HELP
        )

        embed.add_field(
            name="🎯 Game Commands",
            value=(
                "• `/start` or `h!start` — Start a new word in the game channel\n"
                "• `/hint` or `h!hint` — Reveal 1 hidden letter (1 per word per player)\n"
                "• *Type single letters or full words in the game channel to play!*"
            ),
            inline=False
        )
        embed.add_field(
            name="🎵 Music Commands (Lavalink)",
            value=(
                "• `/play <query>` or `h!play` — Play any song or playlist with interactive controls\n"
                "• `/pause` & `/resume` — Pause or resume playback\n"
                "• `/skip [count]` & `/stop` — Skip tracks or stop and leave voice\n"
                "• `/queue` & `/shuffle` — View upcoming queue or randomize order\n"
                "• `/loop [mode]` & `/autoplay` — Cycle repeat modes or toggle continuous autoplay\n"
                "• `/volume <0-200>` — Adjust audio volume\n"
                "• `/nowplaying` — Open interactive button panel (Play, Skip, Loop, Volume, Queue)\n"
                "• `/filter <preset>` — Bass boost, nightcore, 8D audio, or karaoke"
            ),
            inline=False
        )
        embed.add_field(
            name="📊 Stats & Profile Commands",
            value=(
                "• `/profile [@user]` or `h!profile` — View player profile, synced badges & global XP\n"
                "• `/daily` or `h!daily` — View today's server leaderboard\n"
                "• `/weekly` or `h!weekly` — View this week's server leaderboard\n"
                "• `/monthly` or `h!monthly` — View global monthly leaderboard (Top 1 wins Seasonal Badges)\n"
                "• `/serverstats` or `h!serverstats` — View total server games & player stats\n"
                "• `/leaderboard` or `h!lb` — Quick access to server rankings"
            ),
            inline=False
        )
        embed.add_field(
            name="🛡️ Admin Commands",
            value=(
                "• `/setchannel` or `h!setchannel` — Set current channel as game channel\n"
                "• `/skip` or `h!skip` — Skip current word (Server Admins & Mods)"
            ),
            inline=False
        )
        embed.add_field(
            name="🏆 Seasonal Badges & Honors (Synced Across Servers)",
            value=(
                "• 👑 **Monthly Global Champion** — Awarded to the #1 global monthly player\n"
                "• ⚡👨‍💻 **Bot Owner** — Bot creator\n"
                "• 🎃 🎄 🌕 🪔 🎆 💝 🐰 **Seasonal Badges** — Exclusive monthly event badges synced to your profile across all servers!"
            ),
            inline=False
        )
        embed.add_field(
            name="💡 Rules & 8-Hour Timer",
            value="Each player gets **6 lives** (`❤️❤️❤️❤️❤️❤️`). Wrong guesses only penalize the guessing player. If no one cracks a word in **8 hours**, it automatically skips!",
            inline=False
        )

        set_cohesive_style(embed, self.bot.user)
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="profile",
        description="View your global hangman profile, synced seasonal badges, and server XP."
    )
    async def profile(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        target = member or ctx.author
        profile = await get_global_user_profile(target.id)
        srv_stats = await get_user_stats(target.id, ctx.guild.id)
        is_owner = (target.id == BOT_OWNER_ID)

        embed = create_profile_embed(
            member=target,
            profile=profile,
            server_stats=srv_stats,
            is_owner=is_owner,
            bot_user=self.bot.user
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="stats",
        description="Alias for profile: View player statistics and achievements."
    )
    async def stats(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        await self.profile(ctx, member=member)

    @commands.hybrid_command(
        name="daily",
        description="View today's top players on this server."
    )
    async def daily(self, ctx: commands.Context):
        top_players = await get_server_leaderboard(ctx.guild.id, period="daily", limit=10)
        embed = create_leaderboard_embed(
            title="📅 Daily Server Leaderboard",
            description=f"Top performers today in **{ctx.guild.name}**",
            players=top_players,
            xp_field="daily_xp",
            color=COLOR_DAILY,
            footer_text="Daily scores reset every midnight at 00:00 UTC",
            bot_user=self.bot.user
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="weekly",
        description="View this week's top players on this server."
    )
    async def weekly(self, ctx: commands.Context):
        top_players = await get_server_leaderboard(ctx.guild.id, period="weekly", limit=10)
        embed = create_leaderboard_embed(
            title="📆 Weekly Server Leaderboard",
            description=f"Top performers this week in **{ctx.guild.name}**",
            players=top_players,
            xp_field="weekly_xp",
            color=COLOR_WEEKLY,
            footer_text="Weekly scores reset every Sunday at 00:00 UTC",
            bot_user=self.bot.user
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="monthly",
        description="View the global monthly leaderboard across all servers (Top 1 wins Seasonal Badge)."
    )
    async def monthly(self, ctx: commands.Context):
        top_players = await get_global_monthly_leaderboard(limit=10)
        server_count = len(self.bot.guilds)
        embed = create_leaderboard_embed(
            title="🏆 Global Monthly Leaderboard",
            description="Top players across **ALL servers** this month!\nThe #1 Champion receives exclusive seasonal badges synced to their profile.",
            players=top_players,
            xp_field="monthly_xp",
            color=COLOR_MONTHLY,
            footer_text=f"Resets on 1st of each month • {server_count} servers tracked",
            bot_user=self.bot.user
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="leaderboard",
        aliases=["lb", "top"],
        description="Quick access to the server's weekly leaderboard."
    )
    async def leaderboard(self, ctx: commands.Context):
        await self.weekly(ctx)

    @commands.hybrid_command(
        name="serverstats",
        description="View general hangman statistics for this server."
    )
    async def serverstats(self, ctx: commands.Context):
        stats = await get_server_stats(ctx.guild.id)

        embed = discord.Embed(
            title=f"📈 Server Statistics — {ctx.guild.name}",
            description="Overview of hangman participation on this server.\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            color=COLOR_STATS
        )
        embed.add_field(name="👥 Active Players", value=f"**{stats['player_count']}**", inline=True)
        embed.add_field(name="🧩 Words Solved", value=f"**{stats['words_solved']}**", inline=True)
        embed.add_field(name="⭐ Total Server XP", value=f"**{stats['total_xp']:,} XP**", inline=True)

        set_cohesive_style(embed, self.bot.user)
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(StatsCog(bot))
