"""SQLite-backed persistence for in-progress LitStone game sessions."""

from __future__ import annotations

import contextlib
import json
import sqlite3
import time
from typing import Any


class GameStore:
    """Persist active game state so sessions survive server restarts."""

    def __init__(self, db_path: str = "litstone.db") -> None:
        self.db_path = db_path
        self._ensure_schema()

    @contextlib.contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS games (
                    game_id TEXT PRIMARY KEY,
                    state_json TEXT NOT NULL,
                    updated_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS decks (
                    token TEXT NOT NULL,
                    name TEXT NOT NULL,
                    hero_class TEXT NOT NULL,
                    cards_json TEXT NOT NULL,
                    updated_at REAL NOT NULL,
                    PRIMARY KEY (token, name)
                )
                """
            )

    def save(self, game_id: str, state: dict[str, Any]) -> None:
        payload = json.dumps(state)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO games (game_id, state_json, updated_at)
                VALUES (?, ?, ?)
                """,
                (game_id, payload, time.time()),
            )

    def delete(self, game_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM games WHERE game_id = ?", (game_id,))

    def load_all(self) -> dict[str, dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT game_id, state_json FROM games").fetchall()
        games: dict[str, dict[str, Any]] = {}
        for game_id, raw in rows:
            try:
                games[game_id] = json.loads(raw)
            except json.JSONDecodeError:
                continue
        return games

    def count(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) FROM games").fetchone()
        return int(row[0]) if row else 0

    # ---- Account-less deck storage (keyed by a browser token) ----------------

    def save_deck(self, token: str, name: str, hero_class: str, cards: list[str]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO decks (token, name, hero_class, cards_json, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (token, name, hero_class, json.dumps(cards), time.time()),
            )

    def list_decks(self, token: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT name, hero_class, cards_json FROM decks WHERE token = ? ORDER BY updated_at",
                (token,),
            ).fetchall()
        decks: list[dict[str, Any]] = []
        for name, hero_class, cards_json in rows:
            try:
                cards = json.loads(cards_json)
            except json.JSONDecodeError:
                continue
            decks.append({"name": name, "heroClass": hero_class, "cards": cards})
        return decks

    def delete_deck(self, token: str, name: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM decks WHERE token = ? AND name = ?", (token, name))
