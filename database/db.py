import os
import sqlite3
import asyncio
import time
from typing import Optional, List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "hangman.db")

def _get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _init_db_sync():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                game_channel_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS active_game (
                guild_id INTEGER PRIMARY KEY,
                channel_id INTEGER,
                word TEXT,
                category TEXT,
                clue TEXT,
                difficulty TEXT,
                guessed_letters TEXT,
                start_time REAL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS active_players (
                guild_id INTEGER,
                user_id INTEGER,
                user_name TEXT,
                lives INTEGER DEFAULT 6,
                hint_used INTEGER DEFAULT 0,
                PRIMARY KEY (guild_id, user_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id INTEGER,
                guild_id INTEGER,
                user_name TEXT,
                total_xp INTEGER DEFAULT 0,
                daily_xp INTEGER DEFAULT 0,
                weekly_xp INTEGER DEFAULT 0,
                monthly_xp INTEGER DEFAULT 0,
                words_solved INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, guild_id)
            )
        """)
        # Global profiles table synced across all servers for badges and global standing
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS global_profiles (
                user_id INTEGER PRIMARY KEY,
                user_name TEXT,
                badges TEXT DEFAULT '',
                titles TEXT DEFAULT '',
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leaderboard_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                period TEXT,
                top_user_id INTEGER,
                top_user_name TEXT,
                xp INTEGER,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

async def init_db():
    await asyncio.to_thread(_init_db_sync)

# --- Guild Settings ---
def _set_game_channel_sync(guild_id: int, channel_id: int):
    with _get_connection() as conn:
        conn.execute("""
            INSERT INTO guild_settings (guild_id, game_channel_id)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET game_channel_id=excluded.game_channel_id
        """, (guild_id, channel_id))
        conn.commit()

async def set_game_channel(guild_id: int, channel_id: int):
    await asyncio.to_thread(_set_game_channel_sync, guild_id, channel_id)

def _get_game_channel_sync(guild_id: int) -> Optional[int]:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT game_channel_id FROM guild_settings WHERE guild_id = ?", (guild_id,))
        row = cursor.fetchone()
        return row[0] if row else None

async def get_game_channel(guild_id: int) -> Optional[int]:
    return await asyncio.to_thread(_get_game_channel_sync, guild_id)

def _get_all_guild_settings_sync() -> List[Dict[str, Any]]:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM guild_settings WHERE game_channel_id IS NOT NULL")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

async def get_all_guild_settings() -> List[Dict[str, Any]]:
    return await asyncio.to_thread(_get_all_guild_settings_sync)

# --- Active Game ---
def _save_active_game_sync(guild_id: int, channel_id: int, word: str, category: str, clue: str, difficulty: str, guessed_letters: List[str]):
    letters_str = ",".join(sorted(guessed_letters))
    current_time = time.time()
    with _get_connection() as conn:
        conn.execute("""
            INSERT INTO active_game (guild_id, channel_id, word, category, clue, difficulty, guessed_letters, start_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                channel_id=excluded.channel_id,
                word=excluded.word,
                category=excluded.category,
                clue=excluded.clue,
                difficulty=excluded.difficulty,
                guessed_letters=excluded.guessed_letters,
                start_time=excluded.start_time
        """, (guild_id, channel_id, word, category, clue, difficulty, letters_str, current_time))
        conn.commit()

async def save_active_game(guild_id: int, channel_id: int, word: str, category: str, clue: str, difficulty: str, guessed_letters: List[str]):
    await asyncio.to_thread(_save_active_game_sync, guild_id, channel_id, word, category, clue, difficulty, guessed_letters)

def _update_guessed_letters_sync(guild_id: int, guessed_letters: List[str]):
    letters_str = ",".join(sorted(guessed_letters))
    with _get_connection() as conn:
        conn.execute("UPDATE active_game SET guessed_letters = ? WHERE guild_id = ?", (letters_str, guild_id))
        conn.commit()

async def update_guessed_letters(guild_id: int, guessed_letters: List[str]):
    await asyncio.to_thread(_update_guessed_letters_sync, guild_id, guessed_letters)

def _get_active_game_sync(guild_id: int) -> Optional[Dict[str, Any]]:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM active_game WHERE guild_id = ?", (guild_id,))
        row = cursor.fetchone()
        if not row:
            return None
        data = dict(row)
        data["guessed_letters"] = data["guessed_letters"].split(",") if data["guessed_letters"] else []
        return data

async def get_active_game(guild_id: int) -> Optional[Dict[str, Any]]:
    return await asyncio.to_thread(_get_active_game_sync, guild_id)

def _get_stale_active_games_sync(max_age_seconds: float) -> List[Dict[str, Any]]:
    threshold = time.time() - max_age_seconds
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM active_game WHERE start_time <= ?", (threshold,))
        rows = cursor.fetchall()
        result = []
        for r in rows:
            data = dict(r)
            data["guessed_letters"] = data["guessed_letters"].split(",") if data["guessed_letters"] else []
            result.append(data)
        return result

async def get_stale_active_games(max_age_seconds: float = 8 * 3600) -> List[Dict[str, Any]]:
    return await asyncio.to_thread(_get_stale_active_games_sync, max_age_seconds)

def _clear_active_game_sync(guild_id: int):
    with _get_connection() as conn:
        conn.execute("DELETE FROM active_game WHERE guild_id = ?", (guild_id,))
        conn.execute("DELETE FROM active_players WHERE guild_id = ?", (guild_id,))
        conn.commit()

async def clear_active_game(guild_id: int):
    await asyncio.to_thread(_clear_active_game_sync, guild_id)

# --- Active Players ---
def _add_or_get_player_sync(guild_id: int, user_id: int, user_name: str) -> Dict[str, Any]:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM active_players WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
        row = cursor.fetchone()
        if row:
            return dict(row)
        conn.execute("""
            INSERT INTO active_players (guild_id, user_id, user_name, lives, hint_used)
            VALUES (?, ?, ?, 6, 0)
        """, (guild_id, user_id, user_name))
        # Ensure global profile exists
        conn.execute("""
            INSERT INTO global_profiles (user_id, user_name)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET user_name=excluded.user_name
        """, (user_id, user_name))
        conn.commit()
        return {"guild_id": guild_id, "user_id": user_id, "user_name": user_name, "lives": 6, "hint_used": 0, "is_new": True}

async def add_or_get_player(guild_id: int, user_id: int, user_name: str) -> Dict[str, Any]:
    return await asyncio.to_thread(_add_or_get_player_sync, guild_id, user_id, user_name)

def _update_player_lives_sync(guild_id: int, user_id: int, lives: int):
    with _get_connection() as conn:
        conn.execute("UPDATE active_players SET lives = ? WHERE guild_id = ? AND user_id = ?", (lives, guild_id, user_id))
        conn.commit()

async def update_player_lives(guild_id: int, user_id: int, lives: int):
    await asyncio.to_thread(_update_player_lives_sync, guild_id, user_id, lives)

def _mark_hint_used_sync(guild_id: int, user_id: int):
    with _get_connection() as conn:
        conn.execute("UPDATE active_players SET hint_used = 1 WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
        conn.commit()

async def mark_hint_used(guild_id: int, user_id: int):
    await asyncio.to_thread(_mark_hint_used_sync, guild_id, user_id)

def _get_active_players_sync(guild_id: int) -> List[Dict[str, Any]]:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM active_players WHERE guild_id = ?", (guild_id,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

async def get_active_players(guild_id: int) -> List[Dict[str, Any]]:
    return await asyncio.to_thread(_get_active_players_sync, guild_id)

# --- User Stats & XP ---
def _add_user_xp_sync(user_id: int, guild_id: int, user_name: str, xp_gain: int) -> Dict[str, Any]:
    with _get_connection() as conn:
        conn.execute("""
            INSERT INTO user_stats (user_id, guild_id, user_name, total_xp, daily_xp, weekly_xp, monthly_xp, words_solved)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            ON CONFLICT(user_id, guild_id) DO UPDATE SET
                user_name=excluded.user_name,
                total_xp=total_xp + excluded.total_xp,
                daily_xp=daily_xp + excluded.daily_xp,
                weekly_xp=weekly_xp + excluded.weekly_xp,
                monthly_xp=monthly_xp + excluded.monthly_xp,
                words_solved=words_solved + 1
        """, (user_id, guild_id, user_name, xp_gain, xp_gain, xp_gain, xp_gain))

        conn.execute("""
            INSERT INTO global_profiles (user_id, user_name)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET user_name=excluded.user_name
        """, (user_id, user_name))
        conn.commit()

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_stats WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
        row = cursor.fetchone()
        return dict(row)

async def add_user_xp(user_id: int, guild_id: int, user_name: str, xp_gain: int) -> Dict[str, Any]:
    return await asyncio.to_thread(_add_user_xp_sync, user_id, guild_id, user_name, xp_gain)

def _get_user_stats_sync(user_id: int, guild_id: int) -> Optional[Dict[str, Any]]:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_stats WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
        row = cursor.fetchone()
        return dict(row) if row else None

async def get_user_stats(user_id: int, guild_id: int) -> Optional[Dict[str, Any]]:
    return await asyncio.to_thread(_get_user_stats_sync, user_id, guild_id)

def _get_global_user_profile_sync(user_id: int) -> Dict[str, Any]:
    with _get_connection() as conn:
        cursor = conn.cursor()
        # Fetch badges
        cursor.execute("SELECT user_name, badges, titles FROM global_profiles WHERE user_id = ?", (user_id,))
        p_row = cursor.fetchone()
        user_name = p_row["user_name"] if p_row else "Player"
        badges = p_row["badges"] if p_row and p_row["badges"] else ""
        titles = p_row["titles"] if p_row and p_row["titles"] else ""

        # Aggregate totals across all guilds
        cursor.execute("""
            SELECT SUM(total_xp) as total_xp,
                   SUM(daily_xp) as daily_xp,
                   SUM(weekly_xp) as weekly_xp,
                   SUM(monthly_xp) as monthly_xp,
                   SUM(words_solved) as words_solved,
                   COUNT(guild_id) as servers_count
            FROM user_stats
            WHERE user_id = ?
        """, (user_id,))
        agg = cursor.fetchone()

        return {
            "user_id": user_id,
            "user_name": user_name,
            "badges": badges,
            "titles": titles,
            "total_xp": (agg["total_xp"] or 0) if agg else 0,
            "daily_xp": (agg["daily_xp"] or 0) if agg else 0,
            "weekly_xp": (agg["weekly_xp"] or 0) if agg else 0,
            "monthly_xp": (agg["monthly_xp"] or 0) if agg else 0,
            "words_solved": (agg["words_solved"] or 0) if agg else 0,
            "servers_count": (agg["servers_count"] or 0) if agg else 0,
        }

async def get_global_user_profile(user_id: int) -> Dict[str, Any]:
    return await asyncio.to_thread(_get_global_user_profile_sync, user_id)

def _get_server_leaderboard_sync(guild_id: int, period: str, limit: int) -> List[Dict[str, Any]]:
    column_map = {
        "daily": "daily_xp",
        "weekly": "weekly_xp",
        "monthly": "monthly_xp",
        "total": "total_xp"
    }
    col = column_map.get(period, "weekly_xp")
    with _get_connection() as conn:
        cursor = conn.cursor()
        query = f"SELECT * FROM user_stats WHERE guild_id = ? AND {col} > 0 ORDER BY {col} DESC LIMIT ?"
        cursor.execute(query, (guild_id, limit))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

async def get_server_leaderboard(guild_id: int, period: str = "weekly", limit: int = 10) -> List[Dict[str, Any]]:
    return await asyncio.to_thread(_get_server_leaderboard_sync, guild_id, period, limit)

def _get_global_monthly_leaderboard_sync(limit: int) -> List[Dict[str, Any]]:
    with _get_connection() as conn:
        cursor = conn.cursor()
        query = """
            SELECT user_id, user_name, SUM(monthly_xp) as monthly_xp, SUM(total_xp) as total_xp
            FROM user_stats
            GROUP BY user_id
            HAVING monthly_xp > 0
            ORDER BY monthly_xp DESC
            LIMIT ?
        """
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

async def get_global_monthly_leaderboard(limit: int = 10) -> List[Dict[str, Any]]:
    return await asyncio.to_thread(_get_global_monthly_leaderboard_sync, limit)

def _get_server_stats_sync(guild_id: int) -> Dict[str, Any]:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(user_id), SUM(total_xp), SUM(words_solved) FROM user_stats WHERE guild_id = ?", (guild_id,))
        row = cursor.fetchone()
        return {
            "player_count": row[0] or 0,
            "total_xp": row[1] or 0,
            "words_solved": row[2] or 0
        }

async def get_server_stats(guild_id: int) -> Dict[str, Any]:
    return await asyncio.to_thread(_get_server_stats_sync, guild_id)

def _reset_daily_xp_sync():
    with _get_connection() as conn:
        conn.execute("UPDATE user_stats SET daily_xp = 0")
        conn.commit()

async def reset_daily_xp():
    await asyncio.to_thread(_reset_daily_xp_sync)

def _reset_weekly_xp_sync():
    with _get_connection() as conn:
        conn.execute("UPDATE user_stats SET weekly_xp = 0")
        conn.commit()

async def reset_weekly_xp():
    await asyncio.to_thread(_reset_weekly_xp_sync)

def _reset_monthly_xp_sync():
    with _get_connection() as conn:
        conn.execute("UPDATE user_stats SET monthly_xp = 0")
        conn.commit()

async def reset_monthly_xp():
    await asyncio.to_thread(_reset_monthly_xp_sync)

def _record_leaderboard_history_sync(guild_id: int, period: str, top_user_id: int, top_user_name: str, xp: int):
    with _get_connection() as conn:
        conn.execute("""
            INSERT INTO leaderboard_history (guild_id, period, top_user_id, top_user_name, xp)
            VALUES (?, ?, ?, ?, ?)
        """, (guild_id, period, top_user_id, top_user_name, xp))
        conn.commit()

async def record_leaderboard_history(guild_id: int, period: str, top_user_id: int, top_user_name: str, xp: int):
    await asyncio.to_thread(_record_leaderboard_history_sync, guild_id, period, top_user_id, top_user_name, xp)

def _add_global_badge_sync(user_id: int, badge: str):
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT badges FROM global_profiles WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            existing = row["badges"] or ""
            if badge not in existing:
                new_badges = f"{existing} {badge}".strip()
                conn.execute("UPDATE global_profiles SET badges = ? WHERE user_id = ?", (new_badges, user_id))
        else:
            conn.execute("INSERT INTO global_profiles (user_id, badges) VALUES (?, ?)", (user_id, badge))
        conn.commit()

async def add_global_badge(user_id: int, badge: str):
    await asyncio.to_thread(_add_global_badge_sync, user_id, badge)
