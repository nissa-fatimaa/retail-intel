#generic helpers used across the app
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Iterable

from config.settings import CURRENCY_SYMBOL


def fmt_money(value: float | int | None, *, decimals: int = 0) -> str:
    """format number as PKR currency."""
    if value is None:
        return f"{CURRENCY_SYMBOL} -"
    return f"{CURRENCY_SYMBOL} {value:,.{decimals}f}"


def fmt_pct(value: float | None, *, decimals: int = 1, signed: bool = False) -> str:
    if value is None:
        return "-"
    sign = "+" if signed and value > 0 else ""
    return f"{sign}{value:.{decimals}f}%"


def fmt_int(value: float | int | None) -> str:
    if value is None:
        return "—"
    return f"{int(round(float(value))):,}"


def daterange(start: date, end: date) -> Iterable[date]:
    """yield dates from start (inclusive) to end (inclusive)."""
    current = start
    while current <= end:
        yield current
        current = current + timedelta(days=1)


def parse_iso_date(value: str | date | datetime) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.fromisoformat(value).date()


def safe_divide(num: float, denom: float, default: float = 0.0) -> float:
    if not denom:
        return default
    return num / denom


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
