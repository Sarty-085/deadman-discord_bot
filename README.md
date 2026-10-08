# 🎮 Wholesome Bot — General Hangman Discord Bot

A feature-packed, cooperative multiplayer Hangman Discord bot with enigmatic riddle clues, individual lives, XP progression, global profiles with synced seasonal badges, and automated leaderboards.

Supports both **Slash Commands (`/`)** and **Prefix Commands (`h!`)**.

---

## 🌟 Key Features

* **🧠 Enigmatic & Challenging Clues**:
  * 130+ curated words across **Animals**, **Technology**, **Nature**, **Geography**, and **Science**.
  * Challenging, riddle-style and trivia-rich clues that guide players without giving the answer away instantly.
* **⚡ Slash Commands (`/`) & Prefix (`h!`)**:
  * Full dual-command support with automatic Discord tree synchronization on startup.
* **👤 Global Player Profiles & Synced Badges**:
  * `/profile` tracks global total XP, monthly XP, words solved, and awards badges.
  * Badges are **100% globally synced** across every server where the bot is installed!
* **🏆 Monthly Top 1 Seasonal Badges**:
  * Every 1st of the month at 00:00 UTC, the **#1 Global Monthly Champion** wins an exclusive seasonal badge:
    * `🎆 New Year Champion` (Jan)
    * `💝 Valentine Champion` (Feb)
    * `🍀 Spring Equinox Champion` (Mar)
    * `🐰 Easter Blossom Champion` (Apr)
    * `🌸 Spring Bloom Champion` (May)
    * `☀️ Summer Solstice Champion` (Jun)
    * `🎆 Midsummer Star Champion` (Jul)
    * `🌕 Harvest Moon Champion` (Aug)
    * `🍂 Autumn Equinox Champion` (Sep)
    * `🎃 Halloween Phantom Champion` (Oct)
    * `🪔 Festival of Lights Champion` (Nov)
    * `🎄 Winter Frost Champion` (Dec)
* **⏰ 8-Hour Inactivity Auto-Skip**:
  * If a word is not solved within **8 hours**, the bot automatically reveals the secret word and initiates a fresh puzzle.
* **👥 Cooperative Multiplayer with Individual Lives**:
  * Any player typing in the game channel seamlessly joins the active round.
  * Every player has their **own pool of 6 lives** (`❤️❤️❤️❤️❤️❤️`) and 1 hint (`(🔍)`).
  * Wrong guesses only reduce the guessing player's lives. Fallen players (`💀`) sit out until the next round while their teammates continue!
* **🎨 Cohesive & Elegant Embed Aesthetics**:
  * Clean, unified design across all embeds with distinct palette indicators.
* **💾 Complete State Persistence**:
  * Built-in SQLite with background async operations.
  * Games, player lives, hints, and stats persist seamlessly across bot restarts or container reboots.

---

## 📋 Commands

### 🎯 Game Commands (Everyone)
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

## 🚀 Hosting on bot-hosting.net

1. Log into your [bot-hosting.net](https://bot-hosting.net) control panel.
2. Create a new **Python** server.
3. Link this GitHub repo (`https://github.com/Sarty-085/deadman-discord_bot.git`) or upload the files.
4. Set Environment Variables in the Configuration tab (or create a `.env` file):
   * `DISCORD_TOKEN`: Paste your Discord bot token.
   * `BOT_PREFIX`: `h!`
   * `BOT_OWNER_ID`: *(Optional)* Your Discord User ID.
5. In [Discord Developer Portal](https://discord.com/developers/applications), ensure **Message Content Intent** is toggled ON under the **Bot** tab.
6. In the Startup tab, start with:
   ```bash
   python main.py
   ```
7. Use `/setchannel` or `h!setchannel` in your server to begin!

---

## 📜 License
MIT License.
