# 🎮 Wholesome Bot — Hangman & Lavalink Music Discord Bot

A feature-packed, cooperative multiplayer Hangman Discord bot with enigmatic riddle clues, individual lives, XP progression, global profiles with synced seasonal badges, and a **high-performance Lavalink Music system with interactive button controls** (inspired by `engineBotMusic`).

Supports both **Slash Commands (`/`)** and **Prefix Commands (`h!`)**.

---

## 🌟 Key Features

### 🦥 Cooperative Hangman
* **🧠 Enigmatic & Challenging Clues**: 130+ curated words across **Animals**, **Technology**, **Nature**, **Geography**, and **Science** with poetic, trivia-rich clues.
* **👥 Cooperative Multiplayer with Individual Lives**: Every player has their own 6 lives (`❤️❤️❤️❤️❤️❤️`) and 1 hint (`(🔍)`). Wrong guesses only penalize the guesser.
* **👤 Global Player Profiles & Synced Badges**: `/profile` tracks global XP, solved words, and awards badges. Badges are **100% globally synced** across every server!
* **🏆 Monthly Top 1 Seasonal Badges**: Every 1st of the month at 00:00 UTC, the #1 Global Monthly Champion wins an exclusive seasonal event badge (`🎆`, `💝`, `🎃`, `🎄`, etc.).
* **⏰ 8-Hour Inactivity Auto-Skip**: If a word remains unsolved for 8 hours, it automatically reveals and rotates.

### 🎵 Lavalink v4 Music System (EngineBot UI)
* **⏯️ Interactive Control Panel**: Live updating player panel with playback buttons:
  * `⏮️` Restart / Previous
  * `⏯️` Pause / Resume
  * `⏭️` Skip
  * `⏹️` Stop & Disconnect
  * `🔁` Cycle Loop (Off ➔ Track ➔ Queue)
  * `🔀` Shuffle Queue
  * `📜` View Queue
  * `🔊` Adjust Volume (Interactive Modal)
  * `♾️` Toggle Autoplay (Continuous similar tracks)
  * `❤️` Save to Favorites
* **🎛️ Audio DSP Filters**: Real-time filters including **Bass Boost**, **Nightcore**, **8D Audio**, and **Karaoke**.
* **🌐 Universal Sources**: Play from YouTube, Spotify, SoundCloud, Deezer, and direct audio streams.

---

## 📋 Commands

### 🎵 Music Commands (Everyone)
| Slash Command | Prefix Command | Description |
|---|---|---|
| `/play <query>` | `h!play` | Search and play any song or playlist with interactive controls. |
| `/playnext <query>` | `h!playnext` | Queue a track to play immediately after the current song. |
| `/skip [count]` | `h!skip` | Skip the current track (or multiple tracks). |
| `/pause` / `/resume` | `h!pause` / `h!resume` | Pause or resume playback. |
| `/stop` | `h!stop` | Stop music, clear queue, and leave voice channel. |
| `/queue` | `h!queue` | View the current upcoming song queue. |
| `/shuffle` | `h!shuffle` | Randomize the order of waiting tracks. |
| `/loop [mode]` | `h!loop` | Cycle repeat modes: `Off`, `Track`, or `Queue`. |
| `/autoplay` | `h!autoplay` | Toggle automatic playback of similar recommendations. |
| `/volume <0-200>` | `h!volume` | Adjust the player volume (0% to 200%). |
| `/nowplaying` | `h!nowplaying` | Display the interactive music control panel embed. |
| `/filter <preset>` | `h!filter` | Apply audio filters (`bassboost`, `nightcore`, `8d`, `karaoke`, `reset`). |

### 🎯 Hangman Game Commands (Everyone)
| Slash Command | Prefix Command | Description |
|---|---|---|
| `/start` | `h!start` | Starts a new hangman game in the designated game channel. |
| `/hint` | `h!hint` | Reveals one hidden letter from the secret word (1 per player per word). |
| *Type any letter (`A-Z`)* | *(no prefix)* | Guesses that letter (in the game channel). |
| *Type a full word* | *(no prefix)* | Attempts to solve the complete word! |

### 📊 Stats & Profiles (Everyone)
| Slash Command | Prefix Command | Description |
|---|---|---|
| `/profile [@user]` | `h!profile` | View player profile, synced badges, global XP, and server stats. |
| `/daily` | `h!daily` | View today's top players on this server. |
| `/weekly` | `h!weekly` | View this week's server leaderboard. |
| `/monthly` | `h!monthly` | View monthly global leaderboard across all servers (Top 1 wins seasonal badge). |
| `/serverstats` | `h!serverstats` | View server statistics (total players, words cracked, total XP). |
| `/leaderboard` | `h!lb` / `h!top` | Quick access to the weekly server leaderboard. |
| `/help` | `h!help` | Displays the complete bot commands guide. |

### 🛡️ Admin Commands
| Slash Command | Prefix Command | Required Permission | Description |
|---|---|---|---|
| `/setchannel` | `h!setchannel` | `Manage Server` / `Admin` | Sets the current channel as the active game channel. |
| `/skip` | `h!skip` | `Manage Messages` / `Admin` | Skips the current word (Any server admin/moderator). |

---

## 🎧 Setting Up Your Own Lavalink Server on bot-hosting.net

To run music on your bot, you can host your own free private Lavalink server on **bot-hosting.net**:

### Step 1: Create a Lavalink Server on bot-hosting.net
1. Log in to [bot-hosting.net](https://bot-hosting.net).
2. Click **Create Server**.
3. Choose the **Lavalink** server type (or Java 17 / 21).
4. Name your server (e.g. `My Lavalink`) and create it.

### Step 2: Upload the Lavalink Configuration
1. Open your Lavalink server in the bot-hosting.net file manager.
2. Upload the included [`lavalink/application.yml`](lavalink/application.yml) file into the root folder of your Lavalink server.
3. Note your server's assigned **Allocation / Port** (shown on the network/dashboard tab, e.g., `12345`).
4. If your Lavalink port differs from 2333, edit `server.port` in `application.yml` to match your allocated port.
5. Click **Start** to launch your Lavalink server. Once you see `Lavalink is ready to accept connections`, it's live!

### Step 3: Connect Wholesome Bot to Your Lavalink Server
In your Discord Bot's `.env` (or environment variables on bot-hosting.net):
```env
LAVALINK_HOST=your-lavalink-ip-or-subdomain.bothosting.net
LAVALINK_PORT=your_allocated_port
LAVALINK_PASSWORD=youshallnotpass
LAVALINK_SECURE=false
```

---

## 🚀 Hosting the Discord Bot on bot-hosting.net

1. Create a second server on [bot-hosting.net](https://bot-hosting.net) selecting **Python**.
2. Link this GitHub repo (`https://github.com/Sarty-085/deadman-discord_bot.git`) or upload the project files.
3. Set the Environment Variables in the Configuration tab:
   ```env
   DISCORD_TOKEN=your_bot_token_here
   BOT_PREFIX=h!
   BOT_OWNER_ID=your_discord_user_id
   LAVALINK_HOST=your_lavalink_host
   LAVALINK_PORT=your_lavalink_port
   LAVALINK_PASSWORD=youshallnotpass
   LAVALINK_SECURE=false
   ```
4. In [Discord Developer Portal](https://discord.com/developers/applications):
   * Ensure **Message Content Intent** is toggled ON under the **Bot** tab.
   * Ensure the bot has `Connect` and `Speak` voice permissions.
5. Start the server (`python main.py`).
6. Enjoy hangman and high-fidelity music streaming in your Discord server!

---

## 📁 Project Structure

```
deadman-discord_bot/
├── main.py                   # Bot startup & cog loader with slash command sync
├── config.py                 # Configuration & Lavalink environment variables
├── requirements.txt          # Python dependencies (discord.py, wavelink, PyNaCl, etc.)
├── embeds.py                 # Unified cohesive embed styling
├── .env.example              # Environment variables template
├── .gitignore                # Excludes credentials, db, cache & exports
├── README.md                 # Complete documentation & hosting guide
├── lavalink/
│   └── application.yml       # Production-ready Lavalink v4 config for bot-hosting.net
├── database/
│   ├── __init__.py
│   └── db.py                 # Async SQLite database wrapper & queries
├── words/
│   ├── words.json            # 130+ words with enigmatic riddle clues
│   └── word_manager.py       # Word selection, masking, letter tracker, difficulty
└── cogs/
    ├── __init__.py
    ├── game.py               # Hangman engine, message listener, embed renderer, hint
    ├── admin.py              # h!setchannel, h!start, h!skip
    ├── stats.py              # h!stats, h!profile, h!daily, h!weekly, h!monthly, h!help
    ├── scheduler.py          # 00:00 UTC daily Hero of the Day, weekly & monthly resets, 8h skip
    └── music.py              # Lavalink v4 Music system with EngineBot UI button panel
```

---

## 📜 License
MIT License.
