from __future__ import annotations

from datetime import date, timedelta

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config.settings import Theme
from models.product import ProductRepository
from models.sale import SaleRepository
from services.events_service import EventsService
from services.weather_service import WeatherService
from ui.widgets.chart_widget import ChartFrame, plot_line
from ui.widgets.stat_card import StatCard
from utils.helpers import fmt_int, fmt_money


class StaffDashboard(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(18)

        #kpi row
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(16)
        self.kpi_today = StatCard("Today's Revenue", "Rs 0", delta="vs 7-day avg")
        self.kpi_units = StatCard("Units Sold (7d)", "0", delta="rolling weekly")
        self.kpi_low = StatCard("Low Stock Items", "0", delta="below safety threshold", accent=Theme.WARNING)
        self.kpi_weather = StatCard("Today's Weather", "—", delta="from Open-Meteo")
        for c in (self.kpi_today, self.kpi_units, self.kpi_low, self.kpi_weather):
            kpi_row.addWidget(c, 1)
        outer.addLayout(kpi_row)

        #middle (charts and low stock table)
        middle = QHBoxLayout()
        middle.setSpacing(16)

        self.chart = ChartFrame("Sales - last 14 days", height=320)
        middle.addWidget(self.chart, 3)

        self.low_table = self._build_low_stock_table()
        middle.addWidget(self.low_table, 2)

        outer.addLayout(middle, 1)

        #bottom (today's tip card)
        outer.addWidget(self._build_tip_card())

    def _build_low_stock_table(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        v = QVBoxLayout(card)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(10)

        title = QLabel("Restock Alerts")
        title.setProperty("role", "sectionTitle")
        v.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Product", "Category", "On Hand", "Safety"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        v.addWidget(self.table, 1)
        return card

    def _build_tip_card(self) -> QFrame:
        self.tip_card = QFrame()
        self.tip_card.setObjectName("cardElevated")
        h = QHBoxLayout(self.tip_card)
        h.setContentsMargins(20, 16, 20, 16)
        h.setSpacing(14)

        flag = QLabel("OPERATIONS TIP")
        flag.setProperty("role", "badge")
        h.addWidget(flag, 0, Qt.AlignmentFlag.AlignTop)

        self.tip_label = QLabel("Loading today's operations tip...")
        self.tip_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 13.5px;")
        self.tip_label.setWordWrap(True)
        h.addWidget(self.tip_label, 1)
        return self.tip_card

    def refresh(self) -> None:
        revenue_today = SaleRepository.daily_revenue(days=1)
        today_rev = revenue_today[-1][1] if revenue_today else 0.0
        last7 = [r for _, r in SaleRepository.daily_revenue(days=8)[:-1]]
        avg7 = sum(last7) / len(last7) if last7 else 0.0
        delta_pct = ((today_rev - avg7) / avg7 * 100) if avg7 else 0
        self.kpi_today.set_value(fmt_money(today_rev))
        sign = "+" if delta_pct >= 0 else ""
        self.kpi_today.set_delta(f"{sign}{delta_pct:.1f}% vs 7-day avg")

        units7 = SaleRepository.units_total(days=7)
        self.kpi_units.set_value(fmt_int(units7))

        low = ProductRepository.low_stock_items()
        self.kpi_low.set_value(str(len(low)))

        #weather
        wx = WeatherService.get_for_date(date.today())
        if wx:
            self.kpi_weather.set_value(f"{wx.condition}")
            self.kpi_weather.set_delta(
                f"High {wx.temp_max_c:.0f}°C • Low {wx.temp_min_c:.0f}°C • {wx.precipitation_mm:.1f}mm"
            )
        else:
            self.kpi_weather.set_value("—")

        #14-day chart
        revenue_series = SaleRepository.daily_revenue(days=14)
        labels = [d[5:] for d, _ in revenue_series]   # MM-DD
        values = [v for _, v in revenue_series]
        self.chart.clear()
        plot_line(self.chart, labels, values, label="Revenue (PKR)")
        self.chart.ax.set_title("")
        self.chart.draw()

        #low stock table
        self.table.setRowCount(0)
        for p in low[:25]:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(p.name))
            self.table.setItem(row, 1, QTableWidgetItem(p.category_name))
            on_hand = QTableWidgetItem(f"{p.current_stock} {p.unit}")
            if p.current_stock <= p.safety_stock * 0.5:
                on_hand.setForeground(_brush(Theme.DANGER))
            elif p.current_stock <= p.safety_stock:
                on_hand.setForeground(_brush(Theme.WARNING))
            self.table.setItem(row, 2, on_hand)
            self.table.setItem(row, 3, QTableWidgetItem(f"{p.safety_stock} {p.unit}"))

        #operations tip
        upcoming = EventsService.upcoming(days=3)
        if upcoming:
            ev = upcoming[0]
            tip = (
                f"Heads-up: '{ev.name}' is on {ev.event_date}. "
                f"Expected impact: {(ev.impact_factor - 1) * 100:+.0f}% on demand. "
                f"Pre-stock fast movers in beverages & snacks."
            )
        elif wx and wx.condition == "Hot":
            tip = (
                f"Hot day expected ({wx.temp_max_c:.0f}°C). Move chilled drinks, "
                f"juices and ice cream to the cooler-front displays."
            )
        elif wx and wx.condition in {"Heavy Rain", "Light Rain"}:
            tip = (
                f"{wx.condition} forecast. Reduce produce displays exposed to entry doors; "
                f"pre-stock instant noodles and tea."
            )
        else:
            tip = "Inventory levels look balanced. Focus on customer service and shelf rotation today."
        self.tip_label.setText(tip)


def _brush(color_hex: str):
    from PyQt6.QtGui import QBrush, QColor
    return QBrush(QColor(color_hex))
