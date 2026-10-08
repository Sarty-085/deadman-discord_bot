import discord
from discord import app_commands
from discord.ext import commands
import wavelink
import asyncio
from typing import Optional, List, Dict, Any

from config import (
    COLOR_MUSIC,
    LAVALINK_URI,
    LAVALINK_PASSWORD,
    BOT_NAME,
)
from embeds import set_cohesive_style

def format_ms(ms: int) -> str:
    total_seconds = int(ms / 1000)
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"

def make_progress_bar(position_ms: int, length_ms: int, size: int = 15) -> str:
    if length_ms <= 0:
        return f"🔘{'─' * (size - 1)}"
    ratio = min(1.0, max(0.0, position_ms / length_ms))
    filled = int(ratio * size)
    bar = ""
    for i in range(size):
        if i == filled:
            bar += "🔘"
        else:
            bar += "─"
    return bar

class VolumeModal(discord.ui.Modal, title="🔊 Adjust Volume"):
    volume_input = discord.ui.TextInput(
        label="Volume Level (0 - 200)",
        placeholder="Enter a value from 0 to 200 (Default: 100)",
        min_length=1,
        max_length=3,
        required=True
    )

    def __init__(self, player: wavelink.Player, cog: "MusicCog"):
        super().__init__()
        self.player = player
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        try:
            val = int(self.volume_input.value)
            if not 0 <= val <= 200:
                raise ValueError
            await self.player.set_volume(val)
            await interaction.response.send_message(f"🔊 Volume adjusted to **{val}%**", ephemeral=True)
            await self.cog.update_panel_message(self.player)
        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid number between 0 and 200.", ephemeral=True)

class MusicControlView(discord.ui.View):
    def __init__(self, cog: "MusicCog", player: wavelink.Player):
        super().__init__(timeout=None)
        self.cog = cog
        self.player = player
        self.sync_button_states()

    def sync_button_states(self):
        # Update pause/play icon
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if item.custom_id == "music_pause_resume":
                    item.emoji = "▶️" if self.player.paused else "⏸️"
                    item.style = discord.ButtonStyle.success if self.player.paused else discord.ButtonStyle.secondary
                elif item.custom_id == "music_loop":
                    if self.player.queue.mode == wavelink.QueueMode.loop:
                        item.style = discord.ButtonStyle.primary
                        item.label = "Track"
                    elif self.player.queue.mode == wavelink.QueueMode.loop_all:
                        item.style = discord.ButtonStyle.success
                        item.label = "Queue"
                    else:
                        item.style = discord.ButtonStyle.secondary
                        item.label = "Off"
                elif item.custom_id == "music_autoplay":
                    is_auto = (self.player.autoplay == wavelink.AutoPlayMode.enabled)
                    item.style = discord.ButtonStyle.primary if is_auto else discord.ButtonStyle.secondary

    @discord.ui.button(emoji="⏮️", style=discord.ButtonStyle.secondary, custom_id="music_prev", row=0)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.player.current:
            return await interaction.response.send_message("❌ Nothing is playing.", ephemeral=True)
        # Restart current track
        await self.player.seek(0)
        await interaction.response.send_message("⏮️ Restarted current track.", ephemeral=True)
        await self.cog.update_panel_message(self.player)

    @discord.ui.button(emoji="⏸️", style=discord.ButtonStyle.secondary, custom_id="music_pause_resume", row=0)
    async def pause_resume_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.player.paused:
            await self.player.pause(False)
            await interaction.response.send_message("▶️ Resumed playback.", ephemeral=True)
        else:
            await self.player.pause(True)
            await interaction.response.send_message("⏸️ Paused playback.", ephemeral=True)
        self.sync_button_states()
        await self.cog.update_panel_message(self.player)

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary, custom_id="music_skip", row=0)
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.player.current:
            return await interaction.response.send_message("❌ Nothing is playing to skip.", ephemeral=True)
        await self.player.skip(force=True)
        await interaction.response.send_message("⏭️ Skipped track.", ephemeral=True)

    @discord.ui.button(emoji="⏹️", style=discord.ButtonStyle.danger, custom_id="music_stop", row=0)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.player.queue.clear()
        await self.player.disconnect()
        await interaction.response.send_message("⏹️ Music stopped and left voice channel.", ephemeral=True)

    @discord.ui.button(label="Off", emoji="🔁", style=discord.ButtonStyle.secondary, custom_id="music_loop", row=0)
    async def loop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Cycle: normal -> loop (track) -> loop_all (queue) -> normal
        current_mode = self.player.queue.mode
        if current_mode == wavelink.QueueMode.normal:
            self.player.queue.mode = wavelink.QueueMode.loop
            await interaction.response.send_message("🔂 Looping single track.", ephemeral=True)
        elif current_mode == wavelink.QueueMode.loop:
            self.player.queue.mode = wavelink.QueueMode.loop_all
            await interaction.response.send_message("🔁 Looping entire queue.", ephemeral=True)
        else:
            self.player.queue.mode = wavelink.QueueMode.normal
            await interaction.response.send_message("➡️ Loop disabled.", ephemeral=True)
        self.sync_button_states()
        await self.cog.update_panel_message(self.player)

    @discord.ui.button(emoji="🔀", style=discord.ButtonStyle.secondary, custom_id="music_shuffle", row=1)
    async def shuffle_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if len(self.player.queue) < 2:
            return await interaction.response.send_message("❌ Need at least 2 tracks in queue to shuffle.", ephemeral=True)
        self.player.queue.shuffle()
        await interaction.response.send_message("🔀 Queue shuffled successfully!", ephemeral=True)
        await self.cog.update_panel_message(self.player)

    @discord.ui.button(emoji="📜", style=discord.ButtonStyle.secondary, custom_id="music_queue", row=1)
    async def queue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = self.cog.build_queue_embed(self.player)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(emoji="🔊", style=discord.ButtonStyle.secondary, custom_id="music_volume", row=1)
    async def volume_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VolumeModal(self.player, self.cog))

    @discord.ui.button(emoji="♾️", style=discord.ButtonStyle.secondary, custom_id="music_autoplay", row=1)
    async def autoplay_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.player.autoplay == wavelink.AutoPlayMode.enabled:
            self.player.autoplay = wavelink.AutoPlayMode.disabled
            await interaction.response.send_message("♾️ Autoplay disabled.", ephemeral=True)
        else:
            self.player.autoplay = wavelink.AutoPlayMode.enabled
            await interaction.response.send_message("♾️ Autoplay enabled! Continuous similar tracks will play.", ephemeral=True)
        self.sync_button_states()
        await self.cog.update_panel_message(self.player)

    @discord.ui.button(emoji="❤️", style=discord.ButtonStyle.secondary, custom_id="music_favorite", row=1)
    async def favorite_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.player.current:
            return await interaction.response.send_message("❌ Nothing is currently playing.", ephemeral=True)
        track = self.player.current
        await interaction.response.send_message(
            f"❤️ Saved **{track.title}** by *{track.author}* to your favorites list!",
            ephemeral=True
        )

class MusicCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.panel_messages: Dict[int, discord.Message] = {}

    async def cog_load(self):
        # Connect node to Lavalink server
        print(f"[MusicCog] Attempting connection to Lavalink at {LAVALINK_URI} (password: '{LAVALINK_PASSWORD}')")
        node = wavelink.Node(
            uri=LAVALINK_URI,
            password=LAVALINK_PASSWORD
        )
        try:
            await wavelink.Pool.connect(nodes=[node], client=self.bot, cache_capacity=100)
            print(f"[MusicCog] Wavelink pool initiated for {LAVALINK_URI}")
        except Exception as e:
            print(f"[MusicCog] Notice: Could not connect to Lavalink at {LAVALINK_URI}: {e}")

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload):
        print(f"[MusicCog] Successfully connected and authenticated with Lavalink node: {payload.node.identifier}")


    # --- Embed & Panel Helpers ---
    def build_player_embed(self, player: wavelink.Player) -> discord.Embed:
        track = player.current
        if not track:
            embed = discord.Embed(
                title="🎵 Music Player",
                description="No track is currently playing.\nUse `/play <song or link>` to get started!\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                color=COLOR_MUSIC
            )
            return set_cohesive_style(embed, self.bot.user)

        pos_str = format_ms(int(player.position))
        len_str = format_ms(track.length)
        progress = make_progress_bar(int(player.position), track.length, size=14)

        loop_text = "Off"
        if player.queue.mode == wavelink.QueueMode.loop:
            loop_text = "🔂 Single Track"
        elif player.queue.mode == wavelink.QueueMode.loop_all:
            loop_text = "🔁 Entire Queue"

        autoplay_text = "Enabled" if player.autoplay == wavelink.AutoPlayMode.enabled else "Disabled"

        embed = discord.Embed(
            title="🎶 Now Playing",
            description=f"**[{track.title}]({track.uri})**\nby *{track.author}*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            color=COLOR_MUSIC
        )

        if track.artwork:
            embed.set_thumbnail(url=track.artwork)

        embed.add_field(
            name="⏱️ Progress",
            value=f"`{pos_str}` {progress} `{len_str}`",
            inline=False
        )

        embed.add_field(name="🔊 Volume", value=f"`{player.volume}%`", inline=True)
        embed.add_field(name="🔁 Loop Mode", value=f"`{loop_text}`", inline=True)
        embed.add_field(name="♾️ Autoplay", value=f"`{autoplay_text}`", inline=True)

        # Show next 2 tracks waiting in queue
        if len(player.queue) > 0:
            queue_preview = []
            for i, next_track in enumerate(list(player.queue)[:2]):
                queue_preview.append(f"`{i+1}.` **{next_track.title}** ({format_ms(next_track.length)})")
            remaining = len(player.queue) - 2
            if remaining > 0:
                queue_preview.append(f"*... and {remaining} more in queue*")
            embed.add_field(name="📜 Next Up", value="\n".join(queue_preview), inline=False)
        else:
            embed.add_field(name="📜 Next Up", value="*Queue is empty. Use /play to add more!*", inline=False)

        requester = getattr(track, "requester", None)
        footer_note = f"Requested by @{requester.display_name}" if requester else "EngineBot Music System"
        return set_cohesive_style(embed, self.bot.user, footer_note)

    def build_queue_embed(self, player: wavelink.Player) -> discord.Embed:
        embed = discord.Embed(
            title="📜 Current Music Queue",
            description=f"Total tracks in queue: **{len(player.queue)}**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            color=COLOR_MUSIC
        )
        if not player.queue:
            embed.add_field(name="", value="*The queue is completely empty.*", inline=False)
        else:
            lines = []
            for i, track in enumerate(list(player.queue)[:10]):
                lines.append(f"`{i+1}.` **{track.title}** (`{format_ms(track.length)}`)")
            if len(player.queue) > 10:
                lines.append(f"*... and {len(player.queue) - 10} additional tracks*")
            embed.add_field(name="", value="\n".join(lines), inline=False)

        return set_cohesive_style(embed, self.bot.user)

    async def update_panel_message(self, player: wavelink.Player):
        guild_id = player.guild.id
        msg = self.panel_messages.get(guild_id)
        if not msg:
            return
        try:
            embed = self.build_player_embed(player)
            view = MusicControlView(self, player)
            await msg.edit(embed=embed, view=view)
        except Exception:
            pass

    # --- Wavelink Events ---
    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackEventPayload):
        player = payload.player
        if not player:
            return

        channel = getattr(player, "home_channel", None)
        if not channel:
            return

        embed = self.build_player_embed(player)
        view = MusicControlView(self, player)

        # Delete previous panel if exists so it stays at bottom of chat
        old_msg = self.panel_messages.get(player.guild.id)
        if old_msg:
            try:
                await old_msg.delete()
            except Exception:
                pass

        new_msg = await channel.send(embed=embed, view=view)
        self.panel_messages[player.guild.id] = new_msg

    @commands.Cog.listener()
    async def on_wavelink_track_exception(self, payload: wavelink.TrackExceptionEventPayload):
        player = payload.player
        track = payload.track
        err_msg = payload.exception.get("message", "Playback failed") if isinstance(payload.exception, dict) else str(payload.exception)
        print(f"[MusicCog] Track exception on '{track.title}': {err_msg}")

        channel = getattr(player, "home_channel", None) if player else None
        if channel:
            embed = discord.Embed(
                title="⚠️ Playback Notice",
                description=(
                    f"Could not stream **{track.title}**.\n\n"
                    f"**Provider Details:** `{err_msg}`\n\n"
                    "💡 *Tip: If YouTube requires login, link your Google account via OAuth in your Lavalink console, or try a SoundCloud/Spotify track.*"
                ),
                color=0xED4245
            )
            set_cohesive_style(embed, self.bot.user)
            await channel.send(embed=embed)

        if player and not player.queue.is_empty:
            await player.play(player.queue.get())

    @commands.Cog.listener()
    async def on_wavelink_track_stuck(self, payload: wavelink.TrackStuckEventPayload):
        player = payload.player
        track = payload.track
        print(f"[MusicCog] Track stuck on '{track.title}', skipping to next...")
        if player and not player.queue.is_empty:
            await player.play(player.queue.get())

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEventPayload):
        player = payload.player
        if not player:
            return
        if not player.queue and player.autoplay == wavelink.AutoPlayMode.disabled:
            # Wait 60s and disconnect if nobody queued anything
            await asyncio.sleep(60)
            if not player.current and not player.queue:
                await player.disconnect()

    # --- Commands ---
    @commands.hybrid_command(name="play", aliases=["p"], description="Play any song or playlist from YouTube, Spotify, or Soundcloud.")
    @app_commands.describe(query="Song title, artist name, or web link")
    async def play(self, ctx: commands.Context, *, query: str):
        if not ctx.author.voice:
            return await ctx.send("❌ You must be connected to a voice channel to play music!", ephemeral=True)

        await ctx.defer()

        # Connect or get active player
        player: wavelink.Player = ctx.voice_client
        if not player:
            try:
                player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
            except Exception as e:
                return await ctx.send(f"❌ Failed to join voice channel: {e}", ephemeral=True)

        player.home_channel = ctx.channel

        # Clean tracking query parameters (e.g. ?si=...) from YouTube URLs
        search_target = query.strip()
        if "youtu.be/" in search_target or "youtube.com/" in search_target:
            try:
                import urllib.parse
                parsed = urllib.parse.urlparse(search_target)
                if parsed.scheme and parsed.netloc:
                    qs = urllib.parse.parse_qs(parsed.query)
                    filtered_qs = {k: v for k, v in qs.items() if k in ("v", "list", "index", "t")}
                    search_target = urllib.parse.urlunparse((
                        parsed.scheme,
                        parsed.netloc,
                        parsed.path.rstrip("/"),
                        parsed.params,
                        urllib.parse.urlencode(filtered_qs, doseq=True),
                        ""
                    ))
            except Exception:
                search_target = query.strip()

        # Search for tracks with multi-tier fallback
        tracks = None
        search_error = None
        try:
            tracks = await wavelink.Playable.search(search_target)
        except Exception as e:
            search_error = e

        # If direct URL or search failed, attempt SoundCloud fallback
        if not tracks:
            try:
                # If it's a raw name, search SoundCloud directly
                if not search_target.startswith(("http://", "https://")):
                    tracks = await wavelink.Playable.search(search_target, source=wavelink.TrackSource.SoundCloud)
            except Exception:
                pass

        if not tracks:
            err_info = f" ({search_error})" if search_error else ""
            return await ctx.send(
                f"❌ Could not load this track{err_info}.\n"
                "💡 *Tip: Try searching by song name (e.g. `/play Sunflower Post Malone`) or pasting a Spotify/SoundCloud link.*",
                ephemeral=True
            )


        if isinstance(tracks, wavelink.Playlist):
            # Playlist loaded
            for t in tracks:
                t.requester = ctx.author
            added_count = await player.queue.put_wait(tracks)
            await ctx.send(f"✅ Queued **{added_count}** tracks from playlist **{tracks.name}**!")
        else:
            track = tracks[0]
            track.requester = ctx.author
            await player.queue.put_wait(track)
            if player.playing:
                await ctx.send(f"✅ Added to queue: **{track.title}** (`{format_ms(track.length)}`)")

        if not player.playing:
            await player.play(player.queue.get(), volume=100)


    @commands.hybrid_command(name="playnext", description="Queue a track to play immediately after the current song.")
    @app_commands.describe(query="Song title or URL")
    async def playnext(self, ctx: commands.Context, *, query: str):
        if not ctx.author.voice:
            return await ctx.send("❌ You must be in a voice channel!", ephemeral=True)

        player: wavelink.Player = ctx.voice_client
        if not player:
            return await self.play(ctx, query=query)

        tracks = await wavelink.Playable.search(query)
        if not tracks:
            return await ctx.send("❌ No songs found.", ephemeral=True)

        track = tracks[0] if not isinstance(tracks, wavelink.Playlist) else tracks[0]
        track.requester = ctx.author
        player.queue.put_at(0, track)
        await ctx.send(f"⏭️ Next track set to: **{track.title}**")

    @commands.hybrid_command(name="skip", description="Skip the current track or multiple tracks.")
    @app_commands.describe(count="Number of tracks to skip (Default: 1)")
    async def skip(self, ctx: commands.Context, count: Optional[int] = 1):
        player: wavelink.Player = ctx.voice_client
        if not player or not player.current:
            return await ctx.send("❌ No music is currently playing.", ephemeral=True)

        if count and count > 1:
            for _ in range(min(count - 1, len(player.queue))):
                player.queue.delete(0)

        await player.skip(force=True)
        await ctx.send(f"⏭️ Skipped **{count}** track(s).")

    @commands.hybrid_command(name="stop", description="Stop music playback, clear queue, and leave voice channel.")
    async def stop(self, ctx: commands.Context):
        player: wavelink.Player = ctx.voice_client
        if not player:
            return await ctx.send("❌ The bot is not connected to any voice channel.", ephemeral=True)

        player.queue.clear()
        await player.disconnect()
        await ctx.send("⏹️ Playback stopped and disconnected from voice channel.")

    @commands.hybrid_command(name="pause", description="Pause the currently playing track.")
    async def pause(self, ctx: commands.Context):
        player: wavelink.Player = ctx.voice_client
        if not player or not player.playing:
            return await ctx.send("❌ Nothing is currently playing.", ephemeral=True)

        await player.pause(True)
        await ctx.send("⏸️ Paused playback.")
        await self.update_panel_message(player)

    @commands.hybrid_command(name="resume", description="Resume playback if paused.")
    async def resume(self, ctx: commands.Context):
        player: wavelink.Player = ctx.voice_client
        if not player:
            return await ctx.send("❌ No active music player.", ephemeral=True)

        await player.pause(False)
        await ctx.send("▶️ Resumed playback.")
        await self.update_panel_message(player)

    @commands.hybrid_command(name="queue", aliases=["q"], description="View the current music queue.")
    async def queue_cmd(self, ctx: commands.Context):
        player: wavelink.Player = ctx.voice_client
        if not player:
            return await ctx.send("❌ No active player found.", ephemeral=True)
        embed = self.build_queue_embed(player)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="shuffle", description="Randomly shuffle upcoming tracks in queue.")
    async def shuffle(self, ctx: commands.Context):
        player: wavelink.Player = ctx.voice_client
        if not player or len(player.queue) < 2:
            return await ctx.send("❌ Need at least 2 tracks in queue to shuffle.", ephemeral=True)

        player.queue.shuffle()
        await ctx.send("🔀 Shuffled the waiting queue!")
        await self.update_panel_message(player)

    @commands.hybrid_command(name="loop", description="Toggle repeat mode: off, track, or queue.")
    @app_commands.describe(mode="Choose loop mode")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Off", value="off"),
        app_commands.Choice(name="Track", value="track"),
        app_commands.Choice(name="Queue", value="queue"),
    ])
    async def loop(self, ctx: commands.Context, mode: Optional[str] = "track"):
        player: wavelink.Player = ctx.voice_client
        if not player:
            return await ctx.send("❌ No active player.", ephemeral=True)

        if mode == "track":
            player.queue.mode = wavelink.QueueMode.loop
            await ctx.send("🔂 Looping current track.")
        elif mode == "queue":
            player.queue.mode = wavelink.QueueMode.loop_all
            await ctx.send("🔁 Looping entire queue.")
        else:
            player.queue.mode = wavelink.QueueMode.normal
            await ctx.send("➡️ Loop disabled.")

        await self.update_panel_message(player)

    @commands.hybrid_command(name="autoplay", description="Toggle automatic playback of similar recommendations.")
    async def autoplay(self, ctx: commands.Context):
        player: wavelink.Player = ctx.voice_client
        if not player:
            return await ctx.send("❌ No active player.", ephemeral=True)

        if player.autoplay == wavelink.AutoPlayMode.enabled:
            player.autoplay = wavelink.AutoPlayMode.disabled
            await ctx.send("♾️ Autoplay disabled.")
        else:
            player.autoplay = wavelink.AutoPlayMode.enabled
            await ctx.send("♾️ Autoplay enabled! The bot will continue playing similar tracks.")

        await self.update_panel_message(player)

    @commands.hybrid_command(name="volume", aliases=["vol"], description="Adjust playback volume (0 - 200%).")
    @app_commands.describe(level="Volume level percentage (0 to 200)")
    async def volume(self, ctx: commands.Context, level: int):
        player: wavelink.Player = ctx.voice_client
        if not player:
            return await ctx.send("❌ No active player.", ephemeral=True)

        if not 0 <= level <= 200:
            return await ctx.send("❌ Please choose a volume level between 0 and 200.", ephemeral=True)

        await player.set_volume(level)
        await ctx.send(f"🔊 Volume set to **{level}%**")
        await self.update_panel_message(player)

    @commands.hybrid_command(name="nowplaying", aliases=["np", "player"], description="Display the interactive music control panel.")
    async def nowplaying(self, ctx: commands.Context):
        player: wavelink.Player = ctx.voice_client
        if not player or not player.current:
            return await ctx.send("❌ Nothing is currently playing.", ephemeral=True)

        embed = self.build_player_embed(player)
        view = MusicControlView(self, player)
        msg = await ctx.send(embed=embed, view=view)
        self.panel_messages[ctx.guild.id] = msg

    @commands.hybrid_command(name="filter", description="Apply audio filters like bass boost or nightcore.")
    @app_commands.describe(preset="Filter preset name")
    @app_commands.choices(preset=[
        app_commands.Choice(name="Reset (Default)", value="reset"),
        app_commands.Choice(name="Bass Boost", value="bassboost"),
        app_commands.Choice(name="Nightcore", value="nightcore"),
        app_commands.Choice(name="8D Audio", value="8d"),
        app_commands.Choice(name="Karaoke", value="karaoke"),
    ])
    async def filter_cmd(self, ctx: commands.Context, preset: str):
        player: wavelink.Player = ctx.voice_client
        if not player:
            return await ctx.send("❌ No active player.", ephemeral=True)

        filters: wavelink.Filters = player.filters
        if preset == "reset":
            filters.reset()
            await player.set_filters(filters)
            await ctx.send("🎛️ Audio filters reset to default.")
        elif preset == "nightcore":
            filters.timescale.set(speed=1.25, pitch=1.3)
            await player.set_filters(filters)
            await ctx.send("🎛️ Applied **Nightcore** filter (Speed 1.25x, Pitch 1.3x)!")
        elif preset == "8d":
            filters.rotation.set(rotation_hertz=0.2)
            await player.set_filters(filters)
            await ctx.send("🎛️ Applied **8D Audio** rotating filter!")
        elif preset == "karaoke":
            filters.karaoke.set(level=1.0, mono_level=1.0, filter_band=220.0, filter_width=100.0)
            await player.set_filters(filters)
            await ctx.send("🎛️ Applied **Karaoke** vocal dampener filter!")
        elif preset == "bassboost":
            filters.equalizer.set(bands=[
                {"band": 0, "gain": 0.25},
                {"band": 1, "gain": 0.20},
                {"band": 2, "gain": 0.15},
            ])
            await player.set_filters(filters)
            await ctx.send("🎛️ Applied **Bass Boost** equalizer filter!")

        await self.update_panel_message(player)

async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))
