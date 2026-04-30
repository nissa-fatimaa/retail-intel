from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config.settings import Theme
from models.product import Product, ProductRepository
from models.sale import SaleRepository
from services.forecasting_service import ForecastingService, ProductForecast
from ui.widgets.chart_widget import ChartFrame, plot_line, style_axes
from ui.widgets.notification import show_toast
from utils.helpers import fmt_int


class ForecastingPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._products: list[Product] = []
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(18)

        # Controls bar
        ctrl = QFrame()
        ctrl.setObjectName("card")
        ch = QHBoxLayout(ctrl)
        ch.setContentsMargins(20, 14, 20, 14)
        ch.setSpacing(14)

        ch.addWidget(self._field_label("Category"))
        self.cat_combo = QComboBox()
        self.cat_combo.setMinimumWidth(180)
        self.cat_combo.currentIndexChanged.connect(self._on_category_change)
        ch.addWidget(self.cat_combo)

        ch.addWidget(self._field_label("Product"))
        self.product_combo = QComboBox()
        self.product_combo.setMinimumWidth(280)
        self.product_combo.currentIndexChanged.connect(self._refresh_for_selection)
        ch.addWidget(self.product_combo)

        ch.addWidget(self._field_label("Horizon (days)"))
        self.horizon_spin = QSpinBox()
        self.horizon_spin.setRange(3, 14)
        self.horizon_spin.setValue(7)
        self.horizon_spin.valueChanged.connect(self._refresh_for_selection)
        ch.addWidget(self.horizon_spin)

        ch.addStretch(1)
        run_btn = QPushButton("Re-run Forecast")
        run_btn.setProperty("primary", True)
        run_btn.clicked.connect(self._refresh_for_selection)
        ch.addWidget(run_btn)
        outer.addWidget(ctrl)

        #chart row
        self.chart = ChartFrame("Forecast vs recent history", height=320)
        outer.addWidget(self.chart)

        #forecast table and explanations
        bottom = QHBoxLayout()
        bottom.setSpacing(16)
        bottom.addWidget(self._make_table_card(), 3)
        bottom.addWidget(self._make_explanations_card(), 2)
        outer.addLayout(bottom, 1)

    def _field_label(self, text: str) -> QLabel:
        l = QLabel(text)
        l.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; font-weight: 600;")
        return l

    def _make_table_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        v = QVBoxLayout(card)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(10)

        title = QLabel("Daily forecast breakdown")
        title.setProperty("role", "sectionTitle")
        v.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Date", "Day", "Base", "Weather ×", "Event ×", "Forecast"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        v.addWidget(self.table, 1)
        return card

    def _make_explanations_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        v = QVBoxLayout(card)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(10)

        title = QLabel("Why these numbers?")
        title.setProperty("role", "sectionTitle")
        v.addWidget(title)

        self.explanation_box = QLabel("Choose a product to see the reasoning.")
        self.explanation_box.setStyleSheet(
            f"color: {Theme.TEXT_PRIMARY}; font-size: 13px; line-height: 1.6;"
        )
        self.explanation_box.setWordWrap(True)
        self.explanation_box.setAlignment(Qt.AlignmentFlag.AlignTop)
        v.addWidget(self.explanation_box, 1)

        method = QLabel(
            "Method: weighted moving average over the last 14 days, plus a day-of-week "
            "seasonality adjustment, multiplied by transparent weather and event modifiers. "
            "No machine learning is used - every value is reproducible from these inputs."
        )
        method.setProperty("role", "muted")
        method.setWordWrap(True)
        v.addWidget(method)
        return card

    def refresh(self) -> None:
        self._populate_categories()

    def _populate_categories(self) -> None:
        self.cat_combo.blockSignals(True)
        self.cat_combo.clear()
        self.cat_combo.addItem("All categories", None)
        for c in ProductRepository.categories():
            self.cat_combo.addItem(c, c)
        self.cat_combo.blockSignals(False)
        self._on_category_change()

    def _on_category_change(self) -> None:
        cat = self.cat_combo.currentData()
        self._products = (
            ProductRepository.list_all() if cat is None else ProductRepository.by_category(cat)
        )
        self.product_combo.blockSignals(True)
        self.product_combo.clear()
        for p in self._products:
            self.product_combo.addItem(f"{p.name}  ·  {p.category_name}", p.id)
        self.product_combo.blockSignals(False)
        self._refresh_for_selection()

    def _refresh_for_selection(self) -> None:
        if not self._products:
            return
        product_id = self.product_combo.currentData()
        product = next((p for p in self._products if p.id == product_id), self._products[0])

        forecast = ForecastingService.forecast_product(
            product, horizon_days=self.horizon_spin.value()
        )
        self._render(product, forecast)

    def _render(self, product: Product, forecast: ProductForecast) -> None:
        #plot recent 14d history and forecast
        history = SaleRepository.daily_quantity_for_product(product.id, days=14)
        labels = [d[5:] for d, _ in history] + [d.forecast_date[5:] for d in forecast.days]
        values = [q for _, q in history] + [d.final for d in forecast.days]

        self.chart.clear()
        ax = self.chart.ax
        n_history = len(history)
        n_total = len(labels)
        #history line
        ax.plot(
            labels[:n_history],
            values[:n_history],
            color=Theme.ACCENT,
            linewidth=2.0,
            label="Actual",
            marker="o",
            markersize=4,
            markeredgecolor=Theme.BG_SURFACE,
            markerfacecolor=Theme.ACCENT,
        )

        forecast_labels = [labels[n_history - 1]] + labels[n_history:]
        forecast_values = [values[n_history - 1]] + values[n_history:]
        ax.plot(
            forecast_labels,
            forecast_values,
            color=Theme.CYAN,
            linewidth=2.4,
            linestyle="--",
            label="Forecast",
            marker="s",
            markersize=5,
            markeredgecolor=Theme.BG_SURFACE,
            markerfacecolor=Theme.CYAN,
        )
        ax.fill_between(
            forecast_labels, forecast_values, alpha=0.15, color=Theme.CYAN
        )
        ax.set_ylabel("Units / day")
        ax.set_title(f"{product.name} — {product.category_name}", color=Theme.TEXT_PRIMARY)
        ax.legend(loc="best", frameon=False)
        ax.tick_params(axis="x", rotation=35)
        style_axes(ax)
        self.chart.draw()

        #table
        self.table.setRowCount(0)
        from datetime import date as _date
        for d in forecast.days:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(d.forecast_date))
            self.table.setItem(row, 1, QTableWidgetItem(_date.fromisoformat(d.forecast_date).strftime("%a")))
            self.table.setItem(row, 2, QTableWidgetItem(f"{d.base + d.seasonality_adj:.1f}"))
            wm = QTableWidgetItem(f"×{d.weather_multiplier:.2f}")
            if d.weather_multiplier > 1.001:
                wm.setForeground(_brush(Theme.SUCCESS))
            elif d.weather_multiplier < 0.999:
                wm.setForeground(_brush(Theme.WARNING))
            self.table.setItem(row, 3, wm)
            em = QTableWidgetItem(f"×{d.event_multiplier:.2f}")
            if d.event_multiplier > 1.001:
                em.setForeground(_brush(Theme.SUCCESS))
            elif d.event_multiplier < 0.999:
                em.setForeground(_brush(Theme.WARNING))
            self.table.setItem(row, 4, em)
            final = QTableWidgetItem(f"{d.final} {product.unit}")
            final.setForeground(_brush(Theme.CYAN))
            font = final.font()
            font.setBold(True)
            final.setFont(font)
            self.table.setItem(row, 5, final)

        #explanation
        bits: list[str] = []
        bits.append(
            f"<b>Total over {len(forecast.days)} days:</b> {forecast.total_units:,} "
            f"{product.unit} (avg {forecast.avg_per_day:.1f}/day)"
        )
        bits.append("")
        for d in forecast.days[:4]:
            bits.append(f"<b>{d.forecast_date}</b> → {d.final} {product.unit}")
            for ex in d.explanations:
                bits.append(f"  • {ex}")
            bits.append("")
        self.explanation_box.setText("<br>".join(bits))


def _brush(color_hex: str):
    from PyQt6.QtGui import QBrush, QColor
    return QBrush(QColor(color_hex))
