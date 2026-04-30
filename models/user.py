from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from database.db_manager import DatabaseManager


@dataclass
class User:
    id: int
    username: str
    role: str
    full_name: str
    email: str | None = None
    created_at: str | None = None
    last_login: str | None = None

    @classmethod
    def from_row(cls, row) -> "User":
        return cls(
            id=row["id"],
            username=row["username"],
            role=row["role"],
            full_name=row["full_name"],
            email=row["email"],
            created_at=row["created_at"],
            last_login=row["last_login"],
        )


class UserRepository:

    @staticmethod
    def by_username(username: str):
        return DatabaseManager.fetch_one(
            "SELECT * FROM users WHERE username = ?",
            (username,),
        )

    @staticmethod
    def by_id(user_id: int):
        return DatabaseManager.fetch_one(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        )

    @staticmethod
    def create(
        *,
        username: str,
        password_hash: str,
        role: str,
        full_name: str,
        email: str | None = None,
    ) -> int:
        return DatabaseManager.execute(
            """
            INSERT INTO users (username, password_hash, role, full_name, email)
            VALUES (?, ?, ?, ?, ?)
            """,
            (username, password_hash, role, full_name, email),
        )

    @staticmethod
    def update_last_login(user_id: int) -> None:
        DatabaseManager.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (datetime.utcnow().isoformat(timespec="seconds"), user_id),
        )

    @staticmethod
    def count() -> int:
        return DatabaseManager.table_count("users")
