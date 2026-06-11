"""SQLite-backed persistence for in-progress LitStone game sessions."""

from __future__ import annotations

import json
import sqlite3
import time
from typing import Any


class GameStore:
    """Persist active game state so sessions survive server restarts."""

    def __init__(self, db_path: str = "litstone.db") -> None:
        self.db_path = db_path
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

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
