from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from database.db_manager import DatabaseManager


@dataclass
class LocalEvent:
    id: int
    name: str
    event_date: str
    category: str
    expected_attendance: int
    impact_factor: float
    notes: str | None = None


class EventRepository:
    @staticmethod
    def add(
        *,
        name: str,
        event_date: str,
        category: str,
        expected_attendance: int = 0,
        impact_factor: float = 1.0,
        notes: str | None = None,
    ) -> int:
        return DatabaseManager.execute(
            """
            INSERT INTO local_events
                (name, event_date, category, expected_attendance, impact_factor, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, event_date, category, int(expected_attendance), float(impact_factor), notes),
        )

    @staticmethod
    def delete(event_id: int) -> None:
        DatabaseManager.execute("DELETE FROM local_events WHERE id = ?", (event_id,))

    @staticmethod
    def list_all() -> list[LocalEvent]:
        rows = DatabaseManager.fetch_all(
            "SELECT * FROM local_events ORDER BY event_date DESC"
        )
        return [LocalEvent(**{k: r[k] for k in r.keys() if k != "created_at"}) for r in rows]

    @staticmethod
    def upcoming(days: int = 14) -> list[LocalEvent]:
        today = date.today()
        end = today + timedelta(days=days)
        rows = DatabaseManager.fetch_all(
            """
            SELECT * FROM local_events
            WHERE event_date BETWEEN ? AND ?
            ORDER BY event_date
            """,
            (today.isoformat(), end.isoformat()),
        )
        return [LocalEvent(**{k: r[k] for k in r.keys() if k != "created_at"}) for r in rows]

    @staticmethod
    def impact_for_date(target: date) -> float:
        """Combined multiplicative impact factor for events on `target`. 1.0 = no events."""
        rows = DatabaseManager.fetch_all(
            "SELECT impact_factor FROM local_events WHERE event_date = ?",
            (target.isoformat(),),
        )
        impact = 1.0
        for r in rows:
            impact *= float(r["impact_factor"])
        return impact

    @staticmethod
    def events_for_date(target: date) -> list[LocalEvent]:
        rows = DatabaseManager.fetch_all(
            "SELECT * FROM local_events WHERE event_date = ?",
            (target.isoformat(),),
        )
        return [LocalEvent(**{k: r[k] for k in r.keys() if k != "created_at"}) for r in rows]
