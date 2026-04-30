from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config.settings import ROLE_VISITOR, Theme
from models.product import Product, ProductRepository
from ui.widgets.stat_card import StatCard
from utils.helpers import fmt_int, fmt_money


class InventoryPage(QWidget):
    def __init__(self, role: str = ROLE_VISITOR) -> None:
        super().__init__()
        self.role = role
        self._all_products: list[Product] = []

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(180)
        self._search_timer.timeout.connect(self._refresh_table)

        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(16)

        #kpi row
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(14)
        self.kpi_skus = StatCard("Active SKUs", "0")
        self.kpi_value = StatCard("Inventory Value", "Rs 0")
        self.kpi_low = StatCard("Low Stock", "0", accent=Theme.WARNING)
        self.kpi_out = StatCard("Out of Stock", "0", accent=Theme.DANGER)
        for c in (self.kpi_skus, self.kpi_value, self.kpi_low, self.kpi_out):
            kpi_row.addWidget(c, 1)
        outer.addLayout(kpi_row)

        #filters
        ctrl = QFrame()
        ctrl.setObjectName("card")
        ch = QHBoxLayout(ctrl)
        ch.setContentsMargins(20, 14, 20, 14)
        ch.setSpacing(12)

        ch.addWidget(self._field_label("Search"))
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search by name or SKU...")
        self.search.setMinimumWidth(260)
        self.search.textChanged.connect(lambda _t: self._search_timer.start())
        ch.addWidget(self.search)

        ch.addWidget(self._field_label("Category"))
        self.cat_combo = QComboBox()
        self.cat_combo.setMinimumWidth(170)
        self.cat_combo.currentIndexChanged.connect(self._refresh_table)
        ch.addWidget(self.cat_combo)

        ch.addWidget(self._field_label("Stock"))
        self.stock_combo = QComboBox()
        self.stock_combo.addItems(["All", "In stock", "Low", "Out of stock"])
        self.stock_combo.currentIndexChanged.connect(self._refresh_table)
        ch.addWidget(self.stock_combo)
        ch.addStretch(1)
        outer.addWidget(ctrl)

        #table card
        card = QFrame()
        card.setObjectName("card")
        cv = QVBoxLayout(card)
        cv.setContentsMargins(20, 16, 20, 16)
        cv.setSpacing(10)

        title = QLabel("Product catalogue")
        title.setProperty("role", "sectionTitle")
        cv.addWidget(title)

        self.table = QTableWidget()
        self._setup_columns()
        cv.addWidget(self.table, 1)
        outer.addWidget(card, 1)

    def _field_label(self, text: str) -> QLabel:
        l = QLabel(text)
        l.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; font-weight: 600;")
        return l

    def _setup_columns(self) -> None:
        #visitors don't see cost and margin
        if self.role == ROLE_VISITOR:
            headers = ["SKU", "Product", "Category", "Price", "Availability"]
        else:
            headers = ["SKU", "Product", "Category", "On hand", "Safety", "Price", "Cost", "Margin %"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        for i in range(len(headers)):
            mode = QHeaderView.ResizeMode.Stretch if i == 1 else QHeaderView.ResizeMode.ResizeToContents
            self.table.horizontalHeader().setSectionResizeMode(i, mode)

    def refresh(self) -> None:
        self._all_products = ProductRepository.list_all()

        #kpis
        self.kpi_skus.set_value(fmt_int(len(self._all_products)))
        inv_value = sum(p.current_stock * p.cost_price for p in self._all_products)
        self.kpi_value.set_value(fmt_money(inv_value))
        low = [p for p in self._all_products if 0 < p.current_stock <= p.safety_stock]
        out = [p for p in self._all_products if p.current_stock <= 0]
        self.kpi_low.set_value(str(len(low)))
        self.kpi_out.set_value(str(len(out)))

        #categories
        self.cat_combo.blockSignals(True)
        current = self.cat_combo.currentData()
        self.cat_combo.clear()
        self.cat_combo.addItem("All categories", None)
        for c in ProductRepository.categories():
            self.cat_combo.addItem(c, c)
        if current is not None:
            idx = self.cat_combo.findData(current)
            if idx >= 0:
                self.cat_combo.setCurrentIndex(idx)
        self.cat_combo.blockSignals(False)

        self._refresh_table()

    def _refresh_table(self) -> None:
        q = self.search.text().strip().lower()
        cat = self.cat_combo.currentData()
        stock_filter = self.stock_combo.currentText()

        rows = self._all_products
        if q:
            rows = [p for p in rows if q in p.name.lower() or q in p.sku.lower()]
        if cat:
            rows = [p for p in rows if p.category_name == cat]
        if stock_filter == "In stock":
            rows = [p for p in rows if p.current_stock > p.safety_stock]
        elif stock_filter == "Low":
            rows = [p for p in rows if 0 < p.current_stock <= p.safety_stock]
        elif stock_filter == "Out of stock":
            rows = [p for p in rows if p.current_stock <= 0]

        self.table.setRowCount(0)
        for p in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(p.sku))
            self.table.setItem(r, 1, QTableWidgetItem(p.name))
            self.table.setItem(r, 2, QTableWidgetItem(p.category_name))
            if self.role == ROLE_VISITOR:
                self.table.setItem(r, 3, QTableWidgetItem(fmt_money(p.current_price)))
                avail_text, color = _availability(p)
                a_item = QTableWidgetItem(avail_text)
                a_item.setForeground(QBrush(QColor(color)))
                self.table.setItem(r, 4, a_item)
            else:
                stock_item = QTableWidgetItem(f"{p.current_stock} {p.unit}")
                if p.current_stock <= 0:
                    stock_item.setForeground(QBrush(QColor(Theme.DANGER)))
                elif p.current_stock <= p.safety_stock:
                    stock_item.setForeground(QBrush(QColor(Theme.WARNING)))
                self.table.setItem(r, 3, stock_item)
                self.table.setItem(r, 4, QTableWidgetItem(f"{p.safety_stock} {p.unit}"))
                self.table.setItem(r, 5, QTableWidgetItem(fmt_money(p.current_price)))
                self.table.setItem(r, 6, QTableWidgetItem(fmt_money(p.cost_price)))
                margin = (p.current_price - p.cost_price) / p.current_price * 100 if p.current_price else 0
                m_item = QTableWidgetItem(f"{margin:.1f}%")
                if margin < 8:
                    m_item.setForeground(QBrush(QColor(Theme.WARNING)))
                elif margin > 25:
                    m_item.setForeground(QBrush(QColor(Theme.SUCCESS)))
                self.table.setItem(r, 7, m_item)


def _availability(p: Product) -> tuple[str, str]:
    if p.current_stock <= 0:
        return "Out of stock", Theme.DANGER
    if p.current_stock <= p.safety_stock:
        return "Limited", Theme.WARNING
    return "Available", Theme.SUCCESS
