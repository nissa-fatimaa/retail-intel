from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable

from config.settings import DB_PATH, SCHEMA_PATH
from utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:

    @staticmethod
    def initialize() -> None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with DatabaseManager.connect() as conn:
            schema_sql = Path(SCHEMA_PATH).read_text(encoding="utf-8")
            conn.executescript(schema_sql)
            DatabaseManager._migrate(conn)
            conn.commit()
        logger.info("Database initialized at %s", DB_PATH)

    @staticmethod
    def _migrate(conn: sqlite3.Connection) -> None:
        cur = conn.execute("PRAGMA table_info(pricing_history)")
        existing_cols = {row["name"] for row in cur.fetchall()}
        if "reverted" not in existing_cols:
            conn.execute("ALTER TABLE pricing_history ADD COLUMN reverted INTEGER NOT NULL DEFAULT 0")
        if "reverted_at" not in existing_cols:
            conn.execute("ALTER TABLE pricing_history ADD COLUMN reverted_at TEXT")

    @staticmethod
    @contextmanager
    def connect():
        conn = sqlite3.connect(
            str(DB_PATH),
            detect_types=sqlite3.PARSE_DECLTYPES,
            timeout=10.0,
            isolation_level=None,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        try:
            yield conn
        finally:
            conn.close()

    @staticmethod
    def execute(query: str, params: Iterable[Any] | None = None) -> int:
        with DatabaseManager.connect() as conn:
            cur = conn.execute(query, tuple(params or ()))
            conn.commit()
            return cur.lastrowid or cur.rowcount

    @staticmethod
    def executemany(query: str, seq_of_params: Iterable[Iterable[Any]]) -> None:
        with DatabaseManager.connect() as conn:
            conn.executemany(query, [tuple(p) for p in seq_of_params])
            conn.commit()

    @staticmethod
    def fetch_one(query: str, params: Iterable[Any] | None = None) -> sqlite3.Row | None:
        with DatabaseManager.connect() as conn:
            cur = conn.execute(query, tuple(params or ()))
            return cur.fetchone()

    @staticmethod
    def fetch_all(query: str, params: Iterable[Any] | None = None) -> list[sqlite3.Row]:
        with DatabaseManager.connect() as conn:
            cur = conn.execute(query, tuple(params or ()))
            return cur.fetchall()

    @staticmethod
    def table_count(table: str) -> int:
        row = DatabaseManager.fetch_one(f"SELECT COUNT(*) AS c FROM {table}")
        return int(row["c"]) if row else 0
