# 🎮 Wholesome Bot — General Hangman Discord Bot

A feature-packed, cooperative multiplayer Hangman Discord bot with individual lives, clues, XP progression, daily/weekly/monthly leaderboards, and automated champion crowning.

Built with **Python 3.10+** and **discord.py 2.x**, designed to run 24/7 on **bot-hosting.net** with zero external database dependencies.

---

## 🌟 Key Features

* **🧠 General Knowledge Theme with Clues**:
  * Rich curated library of 130+ words spanning **Animals**, **Technology**, **Nature**, **Geography**, and **Science**.
  * Every word includes a helpful **category and clue** in the board embed to guide players!
* **👥 Cooperative Multiplayer with Individual Lives**:
  * Any player typing in the game channel seamlessly joins the active round.
  * Every player has their **own pool of 6 lives** (`❤️❤️❤️❤️❤️❤️`) and 1 hint (`(🔍)`).
  * Wrong guesses only reduce the guessing player's lives. Fallen players (`💀`) sit out until the next round while their teammates continue!
* **💡 Hint System (`h!hint`)**:
  * Reveals an unguessed letter from the secret word.
  * Each player gets 1 hint per word.
* **📈 XP & Word Difficulty Progression**:
  * **Normal Words** (<= 9 letters): `+3` or `+5 XP`
  * **Hard Words** (10-14 letters): `+8 XP` (`🔥 HARD WORD!`)
  * **Expert Words** (15+ letters): `+12 XP` (`🔥🔥 EXPERT WORD!`)
* **🏆 Automated Resets & Crown Events (00:00 UTC)**:
  * **Daily (00:00 UTC)**: Announces **"Hero of the Day"** with a celebratory gold embed and resets daily XP counters.
  * **Weekly (Sunday 00:00 UTC)**: Posts the **Weekly Top 10** leaderboard and resets weekly counters.
  * **Monthly (1st of month 00:00 UTC)**: Crowns **Monthly Global Champions**, awards the exclusive `👑` badge, and resets monthly counters.
* **💾 Complete State Persistence**:
  * Uses built-in SQLite with background async operations.
  * Active games, active players, lives, and XP persist seamlessly across bot restarts or container reboots.

---

## 📋 Commands

### 🎯 Game Commands (Everyone)
| Command | Description |
|---|---|
| `h!start` | Starts a new hangman game in the designated game channel. |
| `h!hint` | Reveals one letter from the secret word (1 hint per player per word). |
| *Type any letter (`A-Z`)* | Guesses that letter (in the game channel). |
| *Type a full word* | Attempts to solve the complete word! |

### 📊 Stats & Leaderboards (Everyone)
| Command | Description |
|---|---|
| `h!stats` or `h!stats @User` | View personal stats (Total XP, Daily XP, Weekly XP, Monthly XP, Words Solved, Badges). |
| `h!daily` | View today's top players in the server. |
| `h!weekly` | View this week's server leaderboard. |
| `h!monthly` | View monthly global leaderboard across all servers. |
| `h!serverstats` | View server statistics (total players, words cracked, total XP). |
| `h!leaderboard` / `h!lb` / `h!top` | Quick access to the weekly server leaderboard. |
| `h!help` | Displays the bot commands guide. |

### 🛡️ Admin Commands
| Command | Required Permission | Description |
|---|---|---|
| `h!setchannel` | `Manage Server` / `Administrator` | Sets the current channel as the active game channel. |
| `h!skip` | `Manage Messages` / `Administrator` | Skips the current word and initiates a new one. |

---

## 🚀 Hosting on bot-hosting.net

Wholesome Bot is optimized out-of-the-box for **bot-hosting.net** (Pterodactyl container hosting):

### Step 1: Create a Bot Application on Discord
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click **New Application**, name it (e.g. `Wholesome Bot`).
3. Navigate to the **Bot** tab:
   * Click **Reset Token** and copy your bot token.
   * Under **Privileged Gateway Intents**, enable **Message Content Intent**.
4. Navigate to **OAuth2 > URL Generator**:
   * Scopes: `bot`
   * Bot Permissions: `Send Messages`, `Embed Links`, `Read Message History`, `Use External Emojis`, `View Channels`.
   * Open the generated link to invite the bot to your server.

### Step 2: Deploy to bot-hosting.net
1. Log into your [bot-hosting.net](https://bot-hosting.net) control panel.
2. Create a new **Python** server.
3. In the file manager:
   * Upload all repository files (or link this GitHub repository).
   * Ensure `main.py` is in the root directory.
4. Set Environment Variables in the Startup/Configuration tab (or create a `.env` file):
   * `DISCORD_TOKEN`: Paste your Discord bot token.
   * `BOT_PREFIX`: `h!`
   * `BOT_OWNER_ID`: *(Optional)* Your Discord User ID.
5. In the **Startup** tab, ensure the start command is:
   ```bash
   python main.py
   ```
6. Start the server! The dependencies from `requirements.txt` will be automatically installed, and the bot will connect.

---

## 💻 Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Sarty-085/deadman-discord_bot.git
   cd deadman-discord_bot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   Create a `.env` file in the project root:
   ```env
   DISCORD_TOKEN=your_token_here
   BOT_PREFIX=h!
   BOT_OWNER_ID=
   ```

4. **Run the bot**:
   ```bash
   python main.py
   ```

5. In your Discord server, type:
   ```
   h!setchannel
   ```
   and start playing!

---

## 📁 Project Structure

```
deadman-discord_bot/
├── main.py                   # Bot startup & cog loader
├── config.py                 # Configuration & environment variables
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── .gitignore                # Excludes credentials, db, cache & exports
├── README.md                 # Complete documentation & hosting guide
├── database/
│   ├── __init__.py
│   └── db.py                 # Async SQLite database wrapper & queries
├── words/
│   ├── words.json            # 130+ general words with clues across 5 categories
│   └── word_manager.py       # Word selection, masking, letter tracker, difficulty
└── cogs/
    ├── __init__.py
    ├── game.py               # Hangman engine, message listener, embed renderer, hint
    ├── admin.py              # h!setchannel, h!start, h!skip
    ├── stats.py              # h!stats, h!daily, h!weekly, h!monthly, h!serverstats, h!help
    └── scheduler.py          # 00:00 UTC daily Hero of the Day, weekly & monthly resets
```

---

## 📜 License
MIT License.
