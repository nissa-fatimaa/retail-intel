from __future__ import annotations

from datetime import date
from typing import Sequence

from models.event import EventRepository, LocalEvent


class EventsService:
    @staticmethod
    def upcoming(days: int = 14) -> list[LocalEvent]:
        return EventRepository.upcoming(days=days)

    @staticmethod
    def list_all() -> list[LocalEvent]:
        return EventRepository.list_all()

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
        return EventRepository.add(
            name=name,
            event_date=event_date,
            category=category,
            expected_attendance=expected_attendance,
            impact_factor=impact_factor,
            notes=notes,
        )

    @staticmethod
    def delete(event_id: int) -> None:
        EventRepository.delete(event_id)

    @staticmethod
    def impact_for_date(target: date) -> tuple[float, list[LocalEvent]]:
        events = EventRepository.events_for_date(target)
        impact = 1.0
        for ev in events:
            impact *= float(ev.impact_factor)
        return impact, events

    @staticmethod
    def impact_summary(events: Sequence[LocalEvent]) -> str | None:
        if not events:
            return None
        if len(events) == 1:
            ev = events[0]
            change = (ev.impact_factor - 1.0) * 100
            sign = "+" if change >= 0 else ""
            return f"Event: {ev.name} ({sign}{change:.0f}%)"
        names = ", ".join(e.name for e in events)
        combined = 1.0
        for e in events:
            combined *= e.impact_factor
        change = (combined - 1.0) * 100
        sign = "+" if change >= 0 else ""
        return f"Events: {names} (combined {sign}{change:.0f}%)"
