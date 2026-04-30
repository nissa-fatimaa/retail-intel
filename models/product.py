from __future__ import annotations

from dataclasses import dataclass

from database.db_manager import DatabaseManager


@dataclass
class Product:
    id: int
    sku: str
    name: str
    category_id: int
    category_name: str
    unit: str
    cost_price: float
    msrp: float
    current_price: float
    current_stock: int
    safety_stock: int
    weather_sensitivity: str
    is_active: bool

    @classmethod
    def from_row(cls, row) -> "Product":
        return cls(
            id=row["id"],
            sku=row["sku"],
            name=row["name"],
            category_id=row["category_id"],
            category_name=row["category_name"] if "category_name" in row.keys() else "",
            unit=row["unit"],
            cost_price=float(row["cost_price"]),
            msrp=float(row["msrp"]),
            current_price=float(row["current_price"]),
            current_stock=int(row["current_stock"]),
            safety_stock=int(row["safety_stock"]),
            weather_sensitivity=row["weather_sensitivity"],
            is_active=bool(row["is_active"]),
        )


_BASE_SELECT = """
    SELECT p.*, c.name AS category_name
    FROM products p
    JOIN categories c ON c.id = p.category_id
"""


class ProductRepository:
    @staticmethod
    def list_all(active_only: bool = True) -> list[Product]:
        sql = _BASE_SELECT
        if active_only:
            sql += " WHERE p.is_active = 1"
        sql += " ORDER BY c.name, p.name"
        rows = DatabaseManager.fetch_all(sql)
        return [Product.from_row(r) for r in rows]

    @staticmethod
    def by_id(product_id: int) -> Product | None:
        row = DatabaseManager.fetch_one(_BASE_SELECT + " WHERE p.id = ?", (product_id,))
        return Product.from_row(row) if row else None

    @staticmethod
    def by_category(category_name: str) -> list[Product]:
        rows = DatabaseManager.fetch_all(
            _BASE_SELECT + " WHERE c.name = ? AND p.is_active = 1 ORDER BY p.name",
            (category_name,),
        )
        return [Product.from_row(r) for r in rows]

    @staticmethod
    def update_price(product_id: int, new_price: float) -> None:
        DatabaseManager.execute(
            "UPDATE products SET current_price = ? WHERE id = ?",
            (round(new_price, 2), product_id),
        )

    @staticmethod
    def update_stock(product_id: int, new_stock: int) -> None:
        DatabaseManager.execute(
            "UPDATE products SET current_stock = ? WHERE id = ?",
            (max(0, int(new_stock)), product_id),
        )

    @staticmethod
    def low_stock_items(threshold_multiplier: float = 1.0) -> list[Product]:
        rows = DatabaseManager.fetch_all(
            _BASE_SELECT
            + " WHERE p.is_active = 1 AND p.current_stock <= p.safety_stock * ?"
            + " ORDER BY (p.current_stock * 1.0 / NULLIF(p.safety_stock, 0)) ASC",
            (threshold_multiplier,),
        )
        return [Product.from_row(r) for r in rows]

    @staticmethod
    def categories() -> list[str]:
        rows = DatabaseManager.fetch_all("SELECT name FROM categories ORDER BY name")
        return [r["name"] for r in rows]
