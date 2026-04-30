from __future__ import annotations

from dataclasses import dataclass

from config.settings import (
    DEFAULT_CATEGORY_ELASTICITY,
    MIN_MARGIN_PCT,
    PRICE_CEILING_MULTIPLIER,
)
from models.product import Product
from services.forecasting_service import ForecastingService, ProductForecast
from utils.helpers import clamp, fmt_money, fmt_pct


@dataclass
class PricingRecommendation:
    product: Product
    forecast: ProductForecast
    current_price: float
    recommended_price: float
    change_pct: float
    tension_index: float
    forecast_units: int
    reason: str
    floor: float
    ceiling: float

    @property
    def action(self) -> str:
        if abs(self.change_pct) < 0.5:
            return "Hold"
        return "Raise" if self.change_pct > 0 else "Lower"


#tension thresholds and the corresponding "target demand multiplier"
#we will pick a target that gently nudges demand toward stock
def _target_price_change(tension: float, elasticity: float) -> float:
    """
    map tension index to a recommended % price change.

    elasticity is negative (e.g. -1.2). To raise/lower demand by ~X%,
    price must change by X / elasticity (will have opposite sign)
    """
    #decide a target % demand change based on tension band.
    if tension >= 1.30:
        target_demand_pct = -12.0   #cool demand by 12%
    elif tension >= 1.10:
        target_demand_pct = -6.0
    elif tension >= 0.90:
        target_demand_pct = 0.0     #balanced so no change
    elif tension >= 0.70:
        target_demand_pct = 6.0
    elif tension >= 0.50:
        target_demand_pct = 10.0
    else:
        target_demand_pct = 15.0

    if target_demand_pct == 0.0 or elasticity == 0:
        return 0.0
    #demand_pct = elasticity * price_pct  =>  price_pct = demand_pct / elasticity
    return target_demand_pct / elasticity


class PricingService:
    @staticmethod
    def recommend(product: Product, *, forecast: ProductForecast | None = None) -> PricingRecommendation:
        if forecast is None:
            forecast = ForecastingService.forecast_product(product)

        forecast_units = forecast.total_units
        stock = max(int(product.current_stock), 1)
        tension = forecast_units / stock

        elasticity = DEFAULT_CATEGORY_ELASTICITY.get(product.category_name, -1.0)

        #target price change driven by tension and elasticity
        raw_change_pct = _target_price_change(tension, elasticity)

        #cap any single recommendation to ±15%
        change_pct = clamp(raw_change_pct, -15.0, 15.0)

        #compute candidate price and clamp to bounds
        floor = round(product.cost_price * (1 + MIN_MARGIN_PCT), 2)
        ceiling = round(product.msrp * PRICE_CEILING_MULTIPLIER, 2)
        candidate = product.current_price * (1 + change_pct / 100.0)
        bounded = clamp(candidate, floor, ceiling)
        actual_change_pct = (bounded / product.current_price - 1.0) * 100.0

        # Build human-readable explanation
        reason = PricingService._build_reason(
            product=product,
            forecast=forecast,
            tension=tension,
            change_pct=actual_change_pct,
            bounded_price=bounded,
            floor=floor,
            ceiling=ceiling,
        )

        return PricingRecommendation(
            product=product,
            forecast=forecast,
            current_price=product.current_price,
            recommended_price=round(bounded, 2),
            change_pct=round(actual_change_pct, 2),
            tension_index=round(tension, 2),
            forecast_units=forecast_units,
            reason=reason,
            floor=floor,
            ceiling=ceiling,
        )

    @staticmethod
    def _build_reason(
        *,
        product: Product,
        forecast: ProductForecast,
        tension: float,
        change_pct: float,
        bounded_price: float,
        floor: float,
        ceiling: float,
    ) -> str:
        bits: list[str] = []

        #stock vs demand
        bits.append(
            f"Forecast next {len(forecast.days)}d: {forecast.total_units} units vs "
            f"stock {product.current_stock} (tension {tension:.2f})"
        )

        #pull primary driver from first day's explanations (weather/events) if present
        primary_drivers = []
        for d in forecast.days[:3]:
            for ex in d.explanations:
                if ex.startswith(("Hot day", "Cold day", "Heavy", "Light", "Event", "Events")):
                    primary_drivers.append(ex)
        seen = set()
        unique_drivers = []
        for ex in primary_drivers:
            if ex not in seen:
                unique_drivers.append(ex)
                seen.add(ex)
            if len(unique_drivers) >= 2:
                break
        if unique_drivers:
            bits.append("Drivers: " + "; ".join(unique_drivers))

        #recommendation
        if abs(change_pct) < 0.5:
            bits.append("Recommendation: hold current price (supply ↔ demand are balanced).")
        elif change_pct > 0:
            bits.append(
                f"Recommendation: increase price by {fmt_pct(change_pct, decimals=1, signed=True)} "
                f"to {fmt_money(bounded_price, decimals=0)}"
            )
        else:
            bits.append(
                f"Recommendation: decrease price by {fmt_pct(change_pct, decimals=1, signed=True)} "
                f"to {fmt_money(bounded_price, decimals=0)}"
            )

        #boundary notes
        if abs(bounded_price - floor) < 0.01 and change_pct < 0:
            bits.append(f"Capped at floor {fmt_money(floor, decimals=0)} (cost + minimum margin).")
        if abs(bounded_price - ceiling) < 0.01 and change_pct > 0:
            bits.append(f"Capped at ceiling {fmt_money(ceiling, decimals=0)} (MSRP × 1.20).")

        return " ".join(bits)
