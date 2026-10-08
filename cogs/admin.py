import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from config import BOT_OWNER_ID
from database import (
    set_game_channel,
    get_game_channel,
    get_active_game,
    clear_active_game
)

class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def is_admin_or_owner(self, member: discord.Member) -> bool:
        if member.id == BOT_OWNER_ID:
            return True
        return member.guild_permissions.manage_guild or member.guild_permissions.administrator

    def can_skip(self, member: discord.Member) -> bool:
        if member.id == BOT_OWNER_ID:
            return True
        return (
            member.guild_permissions.manage_messages
            or member.guild_permissions.manage_guild
            or member.guild_permissions.administrator
        )

    @commands.hybrid_command(
        name="setchannel",
        description="Set the current channel as the active Hangman game channel (Server Admins only)."
    )
    @app_commands.default_permissions(manage_guild=True)
    async def setchannel(self, ctx: commands.Context):
        if not self.is_admin_or_owner(ctx.author):
            await ctx.send("❌ You need Manage Server or Administrator permissions to use this command.", ephemeral=True)
            return

        await set_game_channel(ctx.guild.id, ctx.channel.id)
        await ctx.send("✅ This channel has been set as the Hangman game channel!")

        game = await get_active_game(ctx.guild.id)
        if not game:
            game_cog = self.bot.get_cog("GameCog")
            if game_cog:
                embed = await game_cog.start_new_round(ctx.channel)
                await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="start",
        description="Start a new round of Hangman in the configured game channel."
    )
    async def start(self, ctx: commands.Context):
        configured_channel_id = await get_game_channel(ctx.guild.id)
        if not configured_channel_id:
            await ctx.send("❌ Please set a game channel first using `/setchannel` or `h!setchannel`!", ephemeral=True)
            return

        if ctx.channel.id != configured_channel_id:
            target_ch = ctx.guild.get_channel(configured_channel_id)
            ch_mention = target_ch.mention if target_ch else f"channel ID {configured_channel_id}"
            await ctx.send(f"❌ Games can only be started in the designated game channel: {ch_mention}", ephemeral=True)
            return

        game = await get_active_game(ctx.guild.id)
        if game:
            await ctx.send("❌ A game is already in progress! Finish it first.", ephemeral=True)
            return

        game_cog = self.bot.get_cog("GameCog")
        if game_cog:
            embed = await game_cog.start_new_round(ctx.channel)
            await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="skipword",
        aliases=["skiphangman", "skw"],
        description="Skip the current hangman word (Server Admins & Moderators)."
    )
    @app_commands.default_permissions(manage_messages=True)
    async def skipword(self, ctx: commands.Context):
        if not self.can_skip(ctx.author):
            await ctx.send("❌ You need Manage Messages or Admin permissions to skip words.", ephemeral=True)
            return

        configured_channel_id = await get_game_channel(ctx.guild.id)
        if not configured_channel_id or ctx.channel.id != configured_channel_id:
            await ctx.send("❌ You can only skip words in the active game channel!", ephemeral=True)
            return

        game = await get_active_game(ctx.guild.id)
        if not game:
            await ctx.send("❌ No game is in progress to skip! Use `/start` to begin one.", ephemeral=True)
            return

        word = game["word"]
        await ctx.send(f"⏭️ Skipping word: **{word}**")

        game_cog = self.bot.get_cog("GameCog")
        if game_cog:
            embed = await game_cog.start_new_round(ctx.channel)
            await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))
