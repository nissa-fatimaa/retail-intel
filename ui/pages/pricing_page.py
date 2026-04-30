from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config.settings import Theme
from models.pricing_history import PricingHistoryRepository
from models.product import Product, ProductRepository
from services.forecasting_service import ForecastingService
from services.pricing_service import PricingRecommendation, PricingService
from ui.widgets.notification import show_toast
from utils.helpers import fmt_money, fmt_pct


class PricingPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._recommendations: list[PricingRecommendation] = []
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(16)

        #controls
        ctrl = QFrame()
        ctrl.setObjectName("card")
        ch = QHBoxLayout(ctrl)
        ch.setContentsMargins(20, 14, 20, 14)
        ch.setSpacing(14)

        lab = QLabel("Filter")
        lab.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-weight: 600;")
        ch.addWidget(lab)

        self.cat_combo = QComboBox()
        self.cat_combo.setMinimumWidth(180)
        self.cat_combo.addItem("All categories", None)
        for c in ProductRepository.categories():
            self.cat_combo.addItem(c, c)
        self.cat_combo.currentIndexChanged.connect(self._refresh_table)
        ch.addWidget(self.cat_combo)

        self.action_combo = QComboBox()
        self.action_combo.addItems(["All actions", "Raise only", "Lower only"])
        self.action_combo.currentIndexChanged.connect(self._refresh_table)
        ch.addWidget(self.action_combo)

        ch.addStretch(1)
        recompute = QPushButton("Recompute Recommendations")
        recompute.setProperty("primary", True)
        recompute.clicked.connect(self._recompute)
        ch.addWidget(recompute)
        outer.addWidget(ctrl)

        #recommendations table card
        rec_card = QFrame()
        rec_card.setObjectName("card")
        rv = QVBoxLayout(rec_card)
        rv.setContentsMargins(20, 16, 20, 16)
        rv.setSpacing(10)
        rv.addWidget(self._section("Recommendations"))

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["Product", "Category", "Stock", "7d Demand", "Tension", "Current", "Recommended", "Δ"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self._update_explanation)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 8):
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        rv.addWidget(self.table, 1)
        outer.addWidget(rec_card, 5)

        #bottom row (explanation and actions)
        bottom = QHBoxLayout()
        bottom.setSpacing(16)

        ex_card = QFrame()
        ex_card.setObjectName("card")
        ev = QVBoxLayout(ex_card)
        ev.setContentsMargins(20, 16, 20, 16)
        ev.setSpacing(10)
        ev.addWidget(self._section("Why this recommendation?"))
        self.explanation = QLabel("Select a row to see the explanation.")
        self.explanation.setWordWrap(True)
        self.explanation.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 13px;")
        self.explanation.setAlignment(Qt.AlignmentFlag.AlignTop)
        ev.addWidget(self.explanation, 1)

        boundary = QLabel("")
        boundary.setProperty("role", "muted")
        boundary.setWordWrap(True)
        self.boundary_label = boundary
        ev.addWidget(self.boundary_label)

        bottom.addWidget(ex_card, 3)

        #action card
        act_card = QFrame()
        act_card.setObjectName("cardElevated")
        av = QVBoxLayout(act_card)
        av.setContentsMargins(20, 16, 20, 16)
        av.setSpacing(10)
        av.addWidget(self._section("Apply"))
        info = QLabel(
            "Applying writes the new price into the product catalogue and "
            "logs the change in pricing history."
        )
        info.setProperty("role", "muted")
        info.setWordWrap(True)
        av.addWidget(info)
        av.addStretch(1)
        self.apply_btn = QPushButton("Apply selected recommendation")
        self.apply_btn.setProperty("primary", True)
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self._apply_selected)
        av.addWidget(self.apply_btn)
        bottom.addWidget(act_card, 2)
        outer.addLayout(bottom, 3)

    def _section(self, text: str) -> QLabel:
        l = QLabel(text)
        l.setProperty("role", "sectionTitle")
        return l

    def refresh(self) -> None:
        self._recompute()

    def _recompute(self) -> None:
        products = ProductRepository.list_all()
        forecasts = ForecastingService.forecast_many(products, horizon_days=7)
        self._recommendations = []
        for p, f in zip(products, forecasts):
            try:
                rec = PricingService.recommend(p, forecast=f)
                self._recommendations.append(rec)
            except Exception:
                continue
        self._refresh_table()
        show_toast(self, f"Recomputed {len(self._recommendations)} recommendations.", level="success")

    def _refresh_table(self) -> None:
        cat = self.cat_combo.currentData()
        action_filter = self.action_combo.currentText()

        rows = list(self._recommendations)
        if cat:
            rows = [r for r in rows if r.product.category_name == cat]
        if action_filter == "Raise only":
            rows = [r for r in rows if r.action == "Raise"]
        elif action_filter == "Lower only":
            rows = [r for r in rows if r.action == "Lower"]

        rows.sort(key=lambda r: abs(r.change_pct), reverse=True)

        self.table.setRowCount(0)
        for rec in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(rec.product.name))
            self.table.setItem(r, 1, QTableWidgetItem(rec.product.category_name))
            self.table.setItem(r, 2, QTableWidgetItem(f"{rec.product.current_stock} {rec.product.unit}"))
            self.table.setItem(r, 3, QTableWidgetItem(f"{rec.forecast_units} {rec.product.unit}"))
            tension_item = QTableWidgetItem(f"{rec.tension_index:.2f}")
            if rec.tension_index >= 1.1:
                tension_item.setForeground(_brush(Theme.WARNING))
            elif rec.tension_index <= 0.7:
                tension_item.setForeground(_brush(Theme.INFO))
            self.table.setItem(r, 4, tension_item)
            self.table.setItem(r, 5, QTableWidgetItem(fmt_money(rec.current_price)))
            new_item = QTableWidgetItem(fmt_money(rec.recommended_price))
            new_item.setForeground(_brush(Theme.TEXT_PRIMARY))
            self.table.setItem(r, 6, new_item)
            d_item = QTableWidgetItem(fmt_pct(rec.change_pct, signed=True))
            if rec.change_pct > 0.5:
                d_item.setForeground(_brush(Theme.SUCCESS))
            elif rec.change_pct < -0.5:
                d_item.setForeground(_brush(Theme.WARNING))
            self.table.setItem(r, 7, d_item)
            self.table.item(r, 0).setData(Qt.ItemDataRole.UserRole, id(rec))

        #store filtered
        self._displayed = rows
        if rows:
            self.table.selectRow(0)

    def _update_explanation(self) -> None:
        idx = self.table.currentRow()
        if idx < 0 or idx >= len(self._displayed):
            self.explanation.setText("Select a row to see the explanation.")
            self.boundary_label.setText("")
            self.apply_btn.setEnabled(False)
            return
        rec = self._displayed[idx]
        self.explanation.setText(rec.reason)
        self.boundary_label.setText(
            f"Bounds: floor {fmt_money(rec.floor)} (cost + {int(0.10 * 100)}% margin)  •  "
            f"ceiling {fmt_money(rec.ceiling)} (MSRP × 1.20)."
        )
        self.apply_btn.setEnabled(abs(rec.change_pct) >= 0.5)

    def _apply_selected(self) -> None:
        idx = self.table.currentRow()
        if idx < 0 or idx >= len(self._displayed):
            return
        rec = self._displayed[idx]
        ProductRepository.update_price(rec.product.id, rec.recommended_price)
        record_id = PricingHistoryRepository.add_recommendation(
            product_id=rec.product.id,
            old_price=rec.current_price,
            new_price=rec.recommended_price,
            change_pct=rec.change_pct,
            reason=rec.reason,
        )
        PricingHistoryRepository.mark_applied(record_id)
        show_toast(
            self,
            f"Applied {rec.action.lower()} of {fmt_pct(rec.change_pct, signed=True)} to {rec.product.name}.",
            level="success",
        )
        self._recompute()


def _brush(color_hex: str):
    return QBrush(QColor(color_hex))
