import json
import os
import random
from typing import Dict, Any, List, Tuple

WORDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "words.json")

class WordManager:
    def __init__(self):
        self.words: List[Dict[str, str]] = []
        self.load_words()

    def load_words(self):
        if os.path.exists(WORDS_FILE):
            with open(WORDS_FILE, "r", encoding="utf-8") as f:
                self.words = json.load(f)
        else:
            self.words = []

    def get_difficulty(self, word: str) -> Tuple[str, int, str]:
        """Returns (difficulty_name, xp_reward, display_tag)"""
        clean_len = len(word.replace(" ", "").replace("-", ""))
        if clean_len >= 15:
            return "EXPERT", 12, " 🔥🔥 **EXPERT WORD!**"
        elif clean_len >= 10:
            return "HARD", 8, " 🔥 **HARD WORD!**"
        elif clean_len <= 5:
            return "NORMAL", 3, ""
        else:
            return "NORMAL", 5, ""

    def get_random_word(self) -> Dict[str, Any]:
        item = random.choice(self.words)
        word = item["word"].upper().strip()
        difficulty, xp, tag = self.get_difficulty(word)
        return {
            "word": word,
            "category": item.get("category", "General"),
            "clue": item.get("clue", "A mysterious concept"),
            "difficulty": difficulty,
            "xp": xp,
            "tag": tag,
        }

    @staticmethod
    def format_masked_word(word: str, guessed_letters: List[str]) -> str:
        """
        Formats word for Discord embed:
        Unknown letter: ⬜
        Known letter: uppercase char
        Between letters in a word: 1 space
        Between words: 4 spaces
        """
        guessed_set = set(g.upper() for g in guessed_letters)
        words_list = word.split(" ")
        formatted_words = []
        for w in words_list:
            char_list = []
            for ch in w:
                if ch in ["-", "'", ".", "/"]:
                    char_list.append(ch)
                elif ch.upper() in guessed_set:
                    char_list.append(ch.upper())
                else:
                    char_list.append("⬜")
            formatted_words.append(" ".join(char_list))
        return "    ".join(formatted_words)

    @staticmethod
    def format_guessed_letters(guessed_letters: List[str]) -> str:
        """
        Displays alphabet:
        A  B  C  D  ~~E~~  F ...
        """
        guessed_set = set(g.upper() for g in guessed_letters)
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        display = []
        for ch in alphabet:
            if ch in guessed_set:
                display.append(f"~~{ch}~~")
            else:
                display.append(ch)
        return "  ".join(display)

    @staticmethod
    def is_word_revealed(word: str, guessed_letters: List[str]) -> bool:
        guessed_set = set(g.upper() for g in guessed_letters)
        for ch in word.upper():
            if ch.isalpha() and ch not in guessed_set:
                return False
        return True
