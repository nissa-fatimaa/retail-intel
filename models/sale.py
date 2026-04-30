from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from database.db_manager import DatabaseManager


@dataclass
class Sale:
    id: int
    product_id: int
    sale_date: str
    quantity: int
    unit_price: float
    total: float
    weather_condition: str | None = None


class SaleRepository:
    @staticmethod
    def add(
        *,
        product_id: int,
        sale_date: str,
        quantity: int,
        unit_price: float,
        weather_condition: str | None = None,
    ) -> int:
        total = round(quantity * unit_price, 2)
        return DatabaseManager.execute(
            """
            INSERT INTO sales (product_id, sale_date, quantity, unit_price, total, weather_condition)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (product_id, sale_date, quantity, round(unit_price, 2), total, weather_condition),
        )

    @staticmethod
    def daily_quantity_for_product(product_id: int, days: int = 60) -> list[tuple[str, int]]:
        end = date.today()
        start = end - timedelta(days=days - 1)
        rows = DatabaseManager.fetch_all(
            """
            SELECT sale_date, SUM(quantity) AS qty
            FROM sales
            WHERE product_id = ? AND sale_date >= ?
            GROUP BY sale_date
            """,
            (product_id, start.isoformat()),
        )
        bucket = {r["sale_date"]: int(r["qty"]) for r in rows}
        out: list[tuple[str, int]] = []
        d = start
        while d <= end:
            out.append((d.isoformat(), bucket.get(d.isoformat(), 0)))
            d = d + timedelta(days=1)
        return out

    @staticmethod
    def daily_revenue(days: int = 30) -> list[tuple[str, float]]:
        end = date.today()
        start = end - timedelta(days=days - 1)
        rows = DatabaseManager.fetch_all(
            """
            SELECT sale_date, ROUND(SUM(total), 2) AS revenue
            FROM sales
            WHERE sale_date >= ?
            GROUP BY sale_date
            ORDER BY sale_date
            """,
            (start.isoformat(),),
        )
        bucket = {r["sale_date"]: float(r["revenue"]) for r in rows}
        out: list[tuple[str, float]] = []
        d = start
        while d <= end:
            out.append((d.isoformat(), bucket.get(d.isoformat(), 0.0)))
            d = d + timedelta(days=1)
        return out

    @staticmethod
    def revenue_total(days: int = 30) -> float:
        end = date.today()
        start = end - timedelta(days=days - 1)
        row = DatabaseManager.fetch_one(
            "SELECT COALESCE(SUM(total), 0) AS r FROM sales WHERE sale_date >= ?",
            (start.isoformat(),),
        )
        return float(row["r"]) if row else 0.0

    @staticmethod
    def units_total(days: int = 30) -> int:
        end = date.today()
        start = end - timedelta(days=days - 1)
        row = DatabaseManager.fetch_one(
            "SELECT COALESCE(SUM(quantity), 0) AS u FROM sales WHERE sale_date >= ?",
            (start.isoformat(),),
        )
        return int(row["u"]) if row else 0

    @staticmethod
    def top_products(days: int = 30, limit: int = 10) -> list[dict]:
        end = date.today()
        start = end - timedelta(days=days - 1)
        rows = DatabaseManager.fetch_all(
            """
            SELECT p.id, p.name, c.name AS category, SUM(s.quantity) AS units,
                   ROUND(SUM(s.total), 2) AS revenue
            FROM sales s
            JOIN products p ON p.id = s.product_id
            JOIN categories c ON c.id = p.category_id
            WHERE s.sale_date >= ?
            GROUP BY p.id
            ORDER BY revenue DESC
            LIMIT ?
            """,
            (start.isoformat(), limit),
        )
        return [dict(r) for r in rows]

    @staticmethod
    def revenue_by_category(days: int = 30) -> list[tuple[str, float]]:
        end = date.today()
        start = end - timedelta(days=days - 1)
        rows = DatabaseManager.fetch_all(
            """
            SELECT c.name AS category, ROUND(SUM(s.total), 2) AS revenue
            FROM sales s
            JOIN products p ON p.id = s.product_id
            JOIN categories c ON c.id = p.category_id
            WHERE s.sale_date >= ?
            GROUP BY c.name
            ORDER BY revenue DESC
            """,
            (start.isoformat(),),
        )
        return [(r["category"], float(r["revenue"])) for r in rows]
