import discord
from discord.ext import commands
import random
import re
from typing import Optional, List, Dict, Any

from config import COLOR_GAME
from database import (
    get_game_channel,
    get_active_game,
    save_active_game,
    update_guessed_letters,
    clear_active_game,
    add_or_get_player,
    update_player_lives,
    mark_hint_used,
    get_active_players,
    add_user_xp,
)
from words.word_manager import WordManager

HEARTS = {
    6: "❤️❤️❤️❤️❤️❤️",
    5: "❤️❤️❤️❤️❤️",
    4: "❤️❤️❤️❤️",
    3: "❤️❤️❤️",
    2: "❤️❤️",
    1: "❤️",
    0: "💀"
}

MISS_MESSAGES = {
    5: [
        "❌ Nope, {mention}… watch your step! (❤️❤️❤️❤️❤️)",
        "❌ Nope, {mention}… that was off the mark! (❤️❤️❤️❤️❤️)"
    ],
    4: [
        "❌ Oops, {mention}… that wasn't it! (❤️❤️❤️❤️)",
        "❌ Nope, {mention}… rethink your strategy! (❤️❤️❤️❤️)"
    ],
    3: [
        "❌ Wrong guess, {mention} – stay focused! (❤️❤️❤️)",
        "❌ Nope, {mention}… the letters are slipping away! (❤️❤️❤️)"
    ],
    2: [
        "❌ Nope, {mention}… danger is approaching! (❤️❤️)",
        "❌ Wrong guess, {mention} – tread carefully! (❤️❤️)"
    ],
    1: [
        "❌ Wrong guess, {mention} – only one life left! (❤️)",
        "❌ Nope, {mention}… your last stand has begun! (❤️)"
    ],
    0: [
        "❌ Nope, {mention}… out of lives! (💀)\nHero {mention} has fallen!"
    ]
}

class GameCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.word_manager = WordManager()

    async def create_game_embed(self, guild_id: int) -> Optional[discord.Embed]:
        game = await get_active_game(guild_id)
        if not game:
            return None

        players = await get_active_players(guild_id)

        embed = discord.Embed(
            title="🎯 Hangman — English",
            description="Guess the secret word!\nSimply type one letter or the full word in this channel.",
            color=COLOR_GAME
        )

        # Clue Field
        category = game.get("category", "General")
        clue = game.get("clue", "A mysterious concept.")
        embed.add_field(name="📌 Clue", value=f"**[{category}]** {clue}", inline=False)

        # Lives Field
        if not players:
            lives_value = "😕 No players in this round yet"
        else:
            lines = []
            for p in players:
                u_name = p.get("user_name", "Player")
                lives = p.get("lives", 0)
                hint_used = p.get("hint_used", 0)
                heart_str = HEARTS.get(lives, "💀")
                hint_str = " (🔍)" if (lives > 0 and not hint_used) else ""
                lines.append(f"@{u_name}: {heart_str}{hint_str}")
            lives_value = "\n".join(lines)
        embed.add_field(name="🛡 Lives", value=lives_value, inline=False)

        # Word Field
        masked_word = self.word_manager.format_masked_word(game["word"], game["guessed_letters"])
        embed.add_field(name="🧩 Word", value=masked_word, inline=False)

        # Guessed Letters Field
        letters_display = self.word_manager.format_guessed_letters(game["guessed_letters"])
        embed.add_field(name="🔠 Guessed Letters", value=letters_display, inline=False)

        return embed

    async def start_new_round(self, channel: discord.TextChannel) -> discord.Embed:
        guild_id = channel.guild.id
        await clear_active_game(guild_id)

        item = self.word_manager.get_random_word()
        await save_active_game(
            guild_id=guild_id,
            channel_id=channel.id,
            word=item["word"],
            category=item["category"],
            clue=item["clue"],
            difficulty=item["difficulty"],
            guessed_letters=[]
        )

        embed = await self.create_game_embed(guild_id)
        return embed

    async def handle_word_win(self, channel: discord.TextChannel, user: discord.Member, word: str):
        guild_id = channel.guild.id
        diff_name, xp_reward, tag = self.word_manager.get_difficulty(word)

        stats = await add_user_xp(user.id, guild_id, user.display_name, xp_reward)

        win_msg = (
            f"🎉 All salute you, {user.mention}! You cracked **{word}**!{tag}\n"
            f"**You gain +{xp_reward} XP! Total: {stats['total_xp']} XP | Today: {stats['daily_xp']} XP | This Week: {stats['weekly_xp']} XP**\n"
            f"🧩 **A new mystery awaits! Decipher it!**"
        )
        await channel.send(win_msg)

        # Start next round immediately
        next_embed = await self.start_new_round(channel)
        await channel.send(embed=next_embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # Check if in configured game channel
        configured_channel_id = await get_game_channel(message.guild.id)
        if not configured_channel_id or message.channel.id != configured_channel_id:
            return

        content = message.content.strip()
        if not content:
            return

        # Skip commands
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return

        game = await get_active_game(message.guild.id)
        if not game:
            return

        # Player participation
        player = await add_or_get_player(message.guild.id, message.author.id, message.author.display_name)
        if player.get("is_new"):
            await message.channel.send(f"A new hero enters the battlefield! Welcome, {message.author.mention}!")

        # Check if player has fallen
        if player["lives"] <= 0:
            return

        word = game["word"].upper()
        guessed_letters = set(game["guessed_letters"])

        # Case 1: Single letter guess
        if len(content) == 1 and content.isalpha():
            letter = content.upper()

            # Ignore already guessed letters without penalty
            if letter in guessed_letters:
                return

            guessed_letters.add(letter)
            game["guessed_letters"] = list(guessed_letters)
            await update_guessed_letters(message.guild.id, game["guessed_letters"])

            if letter in word:
                await message.channel.send(f"✅ Hit! The team cheers for you, {message.author.mention}!")
                # Check win
                if self.word_manager.is_word_revealed(word, game["guessed_letters"]):
                    await self.handle_word_win(message.channel, message.author, word)
                    return
            else:
                new_lives = player["lives"] - 1
                await update_player_lives(message.guild.id, message.author.id, new_lives)
                miss_phrase = random.choice(MISS_MESSAGES.get(new_lives, ["❌ Wrong guess!"])).format(mention=message.author.mention)
                await message.channel.send(miss_phrase)

            # Send updated game board
            embed = await self.create_game_embed(message.guild.id)
            if embed:
                await message.channel.send(embed=embed)
            return

        # Case 2: Full word guess
        clean_guess = re.sub(r'[^A-Z]', '', content.upper())
        clean_target = re.sub(r'[^A-Z]', '', word)

        if clean_guess and len(clean_guess) >= 2:
            if clean_guess == clean_target:
                await self.handle_word_win(message.channel, message.author, word)
                return
            else:
                # Wrong word guess penalty
                new_lives = player["lives"] - 1
                await update_player_lives(message.guild.id, message.author.id, new_lives)
                miss_phrase = random.choice(MISS_MESSAGES.get(new_lives, ["❌ Wrong guess!"])).format(mention=message.author.mention)
                await message.channel.send(miss_phrase)

                embed = await self.create_game_embed(message.guild.id)
                if embed:
                    await message.channel.send(embed=embed)

    @commands.command(name="hint")
    async def hint(self, ctx: commands.Context):
        configured_channel_id = await get_game_channel(ctx.guild.id)
        if not configured_channel_id or ctx.channel.id != configured_channel_id:
            return

        game = await get_active_game(ctx.guild.id)
        if not game:
            await ctx.send("❌ No game is currently in progress! Use `h!start` to begin.")
            return

        players = await get_active_players(ctx.guild.id)
        current_player = next((p for p in players if p["user_id"] == ctx.author.id), None)

        if not current_player:
            await ctx.send(f"❌ {ctx.author.mention}, you need to join the game first by making a guess!")
            return

        if current_player["lives"] <= 0:
            await ctx.send(f"❌ {ctx.author.mention}, you're out of lives! You can't use hints.")
            return

        if current_player["hint_used"]:
            await ctx.send(f"❌ {ctx.author.mention}, you've already used your hint for this word!")
            return

        # Find unguessed letters in target word
        word = game["word"].upper()
        guessed_set = set(game["guessed_letters"])
        hidden_letters = [ch for ch in set(word) if ch.isalpha() and ch not in guessed_set]

        if not hidden_letters:
            await ctx.send("All letters have already been revealed!")
            return

        chosen_letter = random.choice(hidden_letters)
        game["guessed_letters"].append(chosen_letter)
        await update_guessed_letters(ctx.guild.id, game["guessed_letters"])
        await mark_hint_used(ctx.guild.id, ctx.author.id)

        await ctx.send(f"💡 Hint for {ctx.author.mention}: The word contains the letter **{chosen_letter}**")

        # Check if hint revealed the entire word
        if self.word_manager.is_word_revealed(word, game["guessed_letters"]):
            await ctx.send(f"✨ The hint revealed the complete word: **{word}**!\n🧩 **A new mystery awaits! Decipher it!**")
            next_embed = await self.start_new_round(ctx.channel)
            await ctx.send(embed=next_embed)
        else:
            embed = await self.create_game_embed(ctx.guild.id)
            if embed:
                await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(GameCog(bot))
