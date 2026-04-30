from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from database.db_manager import DatabaseManager


@dataclass
class PricingRecord:
    id: int
    product_id: int
    product_name: str
    category_name: str | None
    old_price: float
    new_price: float
    change_pct: float
    reason: str
    recommended_at: str
    applied: bool
    applied_at: str | None = None
    reverted: bool = False
    reverted_at: str | None = None

    @property
    def status(self) -> str:
        if self.reverted:
            return "Reverted"
        if self.applied:
            return "Applied"
        return "Suggested"


class PricingHistoryRepository:
    @staticmethod
    def add_recommendation(
        *,
        product_id: int,
        old_price: float,
        new_price: float,
        change_pct: float,
        reason: str,
    ) -> int:
        return DatabaseManager.execute(
            """
            INSERT INTO pricing_history
                (product_id, old_price, new_price, change_pct, reason, applied)
            VALUES (?, ?, ?, ?, ?, 0)
            """,
            (product_id, round(old_price, 2), round(new_price, 2), round(change_pct, 2), reason),
        )

    @staticmethod
    def mark_applied(record_id: int) -> None:
        DatabaseManager.execute(
            "UPDATE pricing_history SET applied = 1, applied_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(timespec="seconds"), record_id),
        )

    @staticmethod
    def mark_reverted(record_id: int) -> None:
        DatabaseManager.execute(
            "UPDATE pricing_history SET reverted = 1, reverted_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(timespec="seconds"), record_id),
        )

    @staticmethod
    def by_id(record_id: int) -> PricingRecord | None:
        row = DatabaseManager.fetch_one(
            """
            SELECT ph.*, p.name AS product_name, c.name AS category_name
            FROM pricing_history ph
            JOIN products p ON p.id = ph.product_id
            LEFT JOIN categories c ON c.id = p.category_id
            WHERE ph.id = ?
            """,
            (record_id,),
        )
        return _from_row(row) if row else None

    @staticmethod
    def list_all(
        *,
        status: str = "all",
        limit: int = 500,
    ) -> list[PricingRecord]:
        clause = ""
        if status == "applied":
            clause = "WHERE ph.applied = 1 AND ph.reverted = 0"
        elif status == "reverted":
            clause = "WHERE ph.reverted = 1"
        elif status == "suggested":
            clause = "WHERE ph.applied = 0 AND ph.reverted = 0"

        rows = DatabaseManager.fetch_all(
            f"""
            SELECT ph.*, p.name AS product_name, c.name AS category_name
            FROM pricing_history ph
            JOIN products p ON p.id = ph.product_id
            LEFT JOIN categories c ON c.id = p.category_id
            {clause}
            ORDER BY ph.recommended_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [_from_row(r) for r in rows]

    @staticmethod
    def recent(limit: int = 50) -> list[PricingRecord]:
        return PricingHistoryRepository.list_all(limit=limit)

    @staticmethod
    def summary() -> dict:
        row = DatabaseManager.fetch_one(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN applied = 1 AND reverted = 0 THEN 1 ELSE 0 END) AS applied_cnt,
                SUM(CASE WHEN reverted = 1 THEN 1 ELSE 0 END) AS reverted_cnt,
                SUM(CASE WHEN applied = 0 AND reverted = 0 THEN 1 ELSE 0 END) AS suggested_cnt
            FROM pricing_history
            """
        )
        if not row:
            return {"total": 0, "applied": 0, "reverted": 0, "suggested": 0}
        return {
            "total": int(row["total"] or 0),
            "applied": int(row["applied_cnt"] or 0),
            "reverted": int(row["reverted_cnt"] or 0),
            "suggested": int(row["suggested_cnt"] or 0),
        }


def _from_row(row) -> PricingRecord:
    return PricingRecord(
        id=row["id"],
        product_id=row["product_id"],
        product_name=row["product_name"],
        category_name=row["category_name"] if "category_name" in row.keys() else None,
        old_price=float(row["old_price"]),
        new_price=float(row["new_price"]),
        change_pct=float(row["change_pct"]),
        reason=row["reason"],
        recommended_at=row["recommended_at"],
        applied=bool(row["applied"]),
        applied_at=row["applied_at"],
        reverted=bool(row["reverted"]) if "reverted" in row.keys() else False,
        reverted_at=row["reverted_at"] if "reverted_at" in row.keys() else None,
    )
