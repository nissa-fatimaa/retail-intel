from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Iterable

from config.settings import FORECAST_HORIZON_DAYS, FORECAST_WINDOW_DAYS
from models.event import LocalEvent
from models.product import Product
from models.sale import SaleRepository
from services.events_service import EventsService
from services.weather_service import DayWeather, WeatherService


@dataclass
class DayForecast:
    forecast_date: str
    base: float                     #historical baseline (1 dp)
    seasonality_adj: float          #additive day-of-week adjustment
    weather_multiplier: float
    event_multiplier: float
    final: int
    weather: DayWeather | None = None
    events: list[LocalEvent] = field(default_factory=list)
    explanations: list[str] = field(default_factory=list)

#most recent samples carry more weight so recency-weighted avg
def _weighted_moving_average(values: list[int], weights: list[float] | None = None) -> float:
    if not values:
        return 0.0
    if weights is None:
        #linear ramp: oldest=1, newest=N
        weights = [float(i + 1) for i in range(len(values))]
    if len(weights) != len(values):
        weights = weights[-len(values):]
    total_w = sum(weights) or 1.0
    return sum(v * w for v, w in zip(values, weights)) / total_w


def _day_of_week_seasonality(values_with_dates: list[tuple[str, int]]) -> dict[int, float]:
    """
    Compute additive day-of-week effect: avg(sales for that DOW) - overall avg.
    Returns dict {weekday(0=Mon): adjustment}.
    """
    if not values_with_dates:
        return {i: 0.0 for i in range(7)}
    overall_avg = sum(v for _, v in values_with_dates) / len(values_with_dates)
    by_dow: dict[int, list[int]] = {i: [] for i in range(7)}
    for d_str, qty in values_with_dates:
        dow = date.fromisoformat(d_str).weekday()
        by_dow[dow].append(qty)
    out = {}
    for dow, vals in by_dow.items():
        if not vals:
            out[dow] = 0.0
            continue
        avg = sum(vals) / len(vals)
        out[dow] = avg - overall_avg
    return out


@dataclass
class ProductForecast:
    product: Product
    days: list[DayForecast]

    @property
    def total_units(self) -> int:
        return sum(d.final for d in self.days)

    @property
    def avg_per_day(self) -> float:
        return self.total_units / len(self.days) if self.days else 0.0


class ForecastingService:
    @staticmethod
    def forecast_product(
        product: Product,
        *,
        horizon_days: int = FORECAST_HORIZON_DAYS,
        window_days: int = FORECAST_WINDOW_DAYS,
        # Optional overrides for the What-If simulator:
        weather_overrides: dict[str, DayWeather] | None = None,
        events_overrides: dict[str, list[LocalEvent]] | None = None,
    ) -> ProductForecast:
        history = SaleRepository.daily_quantity_for_product(product.id, days=window_days)
        recent_qtys = [q for _, q in history]
        base_value = _weighted_moving_average(recent_qtys)
        seasonality = _day_of_week_seasonality(history)

        days: list[DayForecast] = []
        today = date.today()

        for i in range(1, horizon_days + 1):
            target = today + timedelta(days=i)
            target_str = target.isoformat()
            dow = target.weekday()
            seasonal_adj = seasonality.get(dow, 0.0)

            if weather_overrides and target_str in weather_overrides:
                weather = weather_overrides[target_str]
            else:
                weather = WeatherService.get_for_date(target)

            weather_mult, weather_reason = WeatherService.demand_modifier(
                weather, product.weather_sensitivity
            )

            if events_overrides and target_str in events_overrides:
                evs = events_overrides[target_str]
                event_mult = 1.0
                for e in evs:
                    event_mult *= float(e.impact_factor)
            else:
                event_mult, evs = EventsService.impact_for_date(target)

            adjusted_base = max(0.0, base_value + seasonal_adj)
            final = int(round(adjusted_base * weather_mult * event_mult))

            explanations: list[str] = []
            explanations.append(
                f"Baseline (last {window_days}d weighted avg): {base_value:.1f} units/day"
            )
            if abs(seasonal_adj) >= 0.5:
                explanations.append(
                    f"{target.strftime('%A')} effect: {seasonal_adj:+.1f} units"
                )
            if weather_reason:
                explanations.append(weather_reason)
            evt_summary = EventsService.impact_summary(evs)
            if evt_summary:
                explanations.append(evt_summary)

            days.append(
                DayForecast(
                    forecast_date=target_str,
                    base=round(base_value, 1),
                    seasonality_adj=round(seasonal_adj, 2),
                    weather_multiplier=round(weather_mult, 3),
                    event_multiplier=round(event_mult, 3),
                    final=max(0, final),
                    weather=weather,
                    events=list(evs),
                    explanations=explanations,
                )
            )

        return ProductForecast(product=product, days=days)

    @staticmethod
    def forecast_many(
        products: Iterable[Product],
        *,
        horizon_days: int = FORECAST_HORIZON_DAYS,
    ) -> list[ProductForecast]:
        return [
            ForecastingService.forecast_product(p, horizon_days=horizon_days)
            for p in products
        ]
