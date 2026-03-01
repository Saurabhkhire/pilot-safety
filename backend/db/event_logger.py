"""
SQLite session logging and pilot calibration profiles.
"""
from __future__ import annotations

import aiosqlite
import os
import time
from pathlib import Path

from config import config

_db: aiosqlite.Connection | None = None


async def get_connection() -> aiosqlite.Connection:
    global _db
    if _db is None:
        path = Path(config.db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        _db = await aiosqlite.connect(str(path))
        _db.row_factory = aiosqlite.Row
    return _db


async def init_db() -> None:
    schema_path = Path(__file__).parent / "schema.sql"
    if schema_path.exists():
        conn = await get_connection()
        await conn.executescript(schema_path.read_text())
        await conn.commit()


def get_logger() -> "EventLogger":
    """Return logger instance (call after init_db)."""
    return EventLogger()


class EventLogger:
    """Log events and fatigue to DB."""

    async def start_session(self, pilot_id: str | None = None, aircraft_type: str | None = None) -> int:
        conn = await get_connection()
        cursor = await conn.execute(
            "INSERT INTO sessions (started_at, pilot_id, aircraft_type) VALUES (?, ?, ?)",
            (time.time(), pilot_id or "", aircraft_type or ""),
        )
        await conn.commit()
        return cursor.lastrowid or 0

    async def log_event(self, session_id: int, event_type: str, payload: dict | None = None) -> None:
        import json
        conn = await get_connection()
        await conn.execute(
            "INSERT INTO events (session_id, ts, event_type, payload_json) VALUES (?, ?, ?, ?)",
            (session_id, time.time(), event_type, json.dumps(payload) if payload else None),
        )
        await conn.commit()

    async def end_session(self, session_id: int, phase_at_end: str | None = None) -> None:
        conn = await get_connection()
        await conn.execute(
            "UPDATE sessions SET ended_at = ?, phase_at_end = ? WHERE id = ?",
            (time.time(), phase_at_end or "", session_id),
        )
        await conn.commit()
