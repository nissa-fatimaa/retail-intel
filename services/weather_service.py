from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable

import requests

from config.settings import (
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
    DEFAULT_TIMEZONE,
    WEATHER_MODIFIERS,
)
from database.db_manager import DatabaseManager
from utils.logger import get_logger

logger = get_logger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


@dataclass
class DayWeather:
    record_date: str
    temp_max_c: float | None
    temp_min_c: float | None
    precipitation_mm: float | None
    condition: str
    is_forecast: bool

    @property
    def parsed_date(self) -> date:
        return date.fromisoformat(self.record_date)


def _classify_condition(temp_max: float | None, precip_mm: float | None) -> str:
    """Map raw values into a human-readable condition label."""
    if precip_mm is not None and precip_mm >= WEATHER_MODIFIERS["heavy_rain_mm"]:
        return "Heavy Rain"
    if precip_mm is not None and precip_mm >= 1.0:
        return "Light Rain"
    if temp_max is not None and temp_max >= WEATHER_MODIFIERS["hot_day_threshold_c"]:
        return "Hot"
    if temp_max is not None and temp_max <= WEATHER_MODIFIERS["cold_day_threshold_c"]:
        return "Cold"
    return "Mild"


class WeatherService:
    """Fetch weather, persist to DB, and read back."""

    @staticmethod
    def fetch_forecast(days: int = 7) -> list[DayWeather]:
        """Pull a fresh forecast from Open-Meteo and persist it. Falls back to DB."""
        try:
            params = {
                "latitude": DEFAULT_LATITUDE,
                "longitude": DEFAULT_LONGITUDE,
                "timezone": DEFAULT_TIMEZONE,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
                "forecast_days": min(max(days, 1), 16),
            }
            resp = requests.get(OPEN_METEO_URL, params=params, timeout=6)
            resp.raise_for_status()
            data = resp.json().get("daily", {})
            dates = data.get("time", [])
            tmax = data.get("temperature_2m_max", [])
            tmin = data.get("temperature_2m_min", [])
            precip = data.get("precipitation_sum", [])

            out: list[DayWeather] = []
            for i, d in enumerate(dates):
                tmx = tmax[i] if i < len(tmax) else None
                tmn = tmin[i] if i < len(tmin) else None
                pr = precip[i] if i < len(precip) else None
                cond = _classify_condition(tmx, pr)
                out.append(
                    DayWeather(
                        record_date=d,
                        temp_max_c=tmx,
                        temp_min_c=tmn,
                        precipitation_mm=pr,
                        condition=cond,
                        is_forecast=True,
                    )
                )
            WeatherService.persist(out, mark_as_forecast=True)
            return out
        except Exception as exc:  # pragma: no cover - network dependent
            logger.warning("Weather forecast unavailable, falling back to DB: %s", exc)
            return WeatherService.read_range(date.today(), date.today() + timedelta(days=days - 1))

    @staticmethod
    def persist(records: Iterable[DayWeather], *, mark_as_forecast: bool) -> None:
        DatabaseManager.executemany(
            """
            INSERT INTO weather_records
                (record_date, temp_max_c, temp_min_c, precipitation_mm, condition, is_forecast)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(record_date) DO UPDATE SET
                temp_max_c = excluded.temp_max_c,
                temp_min_c = excluded.temp_min_c,
                precipitation_mm = excluded.precipitation_mm,
                condition = excluded.condition,
                is_forecast = excluded.is_forecast
            """,
            (
                (
                    r.record_date,
                    r.temp_max_c,
                    r.temp_min_c,
                    r.precipitation_mm,
                    r.condition,
                    1 if mark_as_forecast else 0,
                )
                for r in records
            ),
        )

    @staticmethod
    def read_range(start: date, end: date) -> list[DayWeather]:
        rows = DatabaseManager.fetch_all(
            """
            SELECT * FROM weather_records
            WHERE record_date BETWEEN ? AND ?
            ORDER BY record_date
            """,
            (start.isoformat(), end.isoformat()),
        )
        return [
            DayWeather(
                record_date=r["record_date"],
                temp_max_c=r["temp_max_c"],
                temp_min_c=r["temp_min_c"],
                precipitation_mm=r["precipitation_mm"],
                condition=r["condition"],
                is_forecast=bool(r["is_forecast"]),
            )
            for r in rows
        ]

    @staticmethod
    def get_for_date(target: date) -> DayWeather | None:
        rows = WeatherService.read_range(target, target)
        return rows[0] if rows else None

    @staticmethod
    def demand_modifier(weather: DayWeather | None, sensitivity: str) -> tuple[float, str | None]:
        """
        Return (multiplier, reason) for a product with the given sensitivity, given the weather.
        sensitivity: 'none' | 'hot' | 'cold' | 'rain'
        """
        if weather is None or sensitivity == "none":
            return 1.0, None

        cond = weather.condition or ""
        tmx = weather.temp_max_c or 0.0
        precip = weather.precipitation_mm or 0.0

        if sensitivity == "hot" and tmx >= WEATHER_MODIFIERS["hot_day_threshold_c"]:
            extra = min(0.35, 0.02 * (tmx - WEATHER_MODIFIERS["hot_day_threshold_c"]) + 0.10)
            return 1.0 + extra, f"Hot day ({tmx:.0f}°C) → +{extra * 100:.0f}%"
        if sensitivity == "cold" and tmx <= WEATHER_MODIFIERS["cold_day_threshold_c"]:
            extra = min(0.30, 0.02 * (WEATHER_MODIFIERS["cold_day_threshold_c"] - tmx) + 0.10)
            return 1.0 + extra, f"Cold day ({tmx:.0f}°C) → +{extra * 100:.0f}%"
        if sensitivity == "rain" and precip >= 1.0:
            extra = min(0.30, 0.02 * precip + 0.05)
            return 1.0 + extra, f"{cond} ({precip:.1f}mm) → +{extra * 100:.0f}%"

        #slight negative effect when conditions hurt foot traffic (heavy rain hurts most)
        if cond == "Heavy Rain" and sensitivity != "rain":
            return 0.92, "Heavy rain reduces foot traffic → -8%"

        return 1.0, None
