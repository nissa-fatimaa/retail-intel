from __future__ import annotations

from datetime import date, timedelta

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from config.settings import APP_NAME, DEFAULT_CITY, Theme
from models.product import ProductRepository
from models.sale import SaleRepository
from services.events_service import EventsService
from services.weather_service import WeatherService
from ui.widgets.chart_widget import ChartFrame, plot_donut, plot_bar
from ui.widgets.stat_card import StatCard
from utils.helpers import fmt_int, fmt_money


class VisitorDashboard(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(18)

        # Hero card
        hero = QFrame()
        hero.setObjectName("card")
        hero.setMinimumHeight(160)
        hv = QVBoxLayout(hero)
        hv.setContentsMargins(28, 22, 28, 22)
        hv.setSpacing(8)

        eyebrow = QLabel(f"BAHRIA FRESH MART — {DEFAULT_CITY.upper()}")
        eyebrow.setStyleSheet(
            f"color: {Theme.CYAN}; font-size: 11px; font-weight: 700; letter-spacing: 1.6px;"
        )
        hv.addWidget(eyebrow)

        self.hero_title = QLabel("Welcome to your local store dashboard.")
        self.hero_title.setProperty("role", "loginHero")
        hv.addWidget(self.hero_title)

        self.hero_subtitle = QLabel("")
        self.hero_subtitle.setProperty("role", "loginTagline")
        self.hero_subtitle.setWordWrap(True)
        hv.addWidget(self.hero_subtitle)

        outer.addWidget(hero)

        #quick stat row
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(16)
        self.kpi_weather = StatCard("Weather Today", "—")
        self.kpi_event = StatCard("Next Local Event", "—")
        self.kpi_units = StatCard("Items Sold This Week", "0")
        for c in (self.kpi_weather, self.kpi_event, self.kpi_units):
            kpi_row.addWidget(c, 1)
        outer.addLayout(kpi_row)

        #charts row
        charts = QHBoxLayout()
        charts.setSpacing(16)

        self.cat_chart = ChartFrame("What's selling — by category (last 30 days)", height=320)
        charts.addWidget(self.cat_chart, 1)

        self.bestsellers = ChartFrame("Top picks this week", height=320)
        charts.addWidget(self.bestsellers, 1)

        outer.addLayout(charts, 1)

    def refresh(self) -> None:
        wx = WeatherService.get_for_date(date.today())
        if wx:
            self.kpi_weather.set_value(wx.condition)
            self.kpi_weather.set_delta(
                f"{wx.temp_min_c:.0f}–{wx.temp_max_c:.0f}°C • {wx.precipitation_mm:.1f}mm rain"
            )

        upcoming = EventsService.upcoming(days=14)
        if upcoming:
            ev = upcoming[0]
            self.kpi_event.set_value(ev.name[:32] + ("…" if len(ev.name) > 32 else ""))
            self.kpi_event.set_delta(f"{ev.event_date} • {ev.category}")
        else:
            self.kpi_event.set_value("Nothing scheduled")
            self.kpi_event.set_delta("Quiet week ahead")

        units7 = SaleRepository.units_total(days=7)
        self.kpi_units.set_value(fmt_int(units7))

        #subtitle reacts to weather/events
        msg_bits = []
        if wx and wx.condition == "Hot":
            msg_bits.append("Stay cool - chilled drinks and ice cream are at the front today.")
        elif wx and wx.condition in {"Heavy Rain", "Light Rain"}:
            msg_bits.append("Cozy weather calls for warm tea, soup mixes and snacks.")
        elif wx and wx.condition == "Cold":
            msg_bits.append("Cold day vibes - fresh bakery and tea selection are stocked.")
        else:
            msg_bits.append("A pleasant day to shop fresh produce and pantry essentials.")
        if upcoming:
            ev = upcoming[0]
            msg_bits.append(f"Heads-up: '{ev.name}' on {ev.event_date}.")
        self.hero_subtitle.setText(" ".join(msg_bits))

        #charts
        cat_rev = SaleRepository.revenue_by_category(days=30)
        self.cat_chart.clear()
        if cat_rev:
            labels = [c for c, _ in cat_rev]
            values = [v for _, v in cat_rev]
            plot_donut(self.cat_chart, labels, values)
        self.cat_chart.draw()

        top = SaleRepository.top_products(days=7, limit=8)
        self.bestsellers.clear()
        if top:
            labels = [t["name"][:18] + ("…" if len(t["name"]) > 18 else "") for t in top]
            values = [t["units"] for t in top]
            plot_bar(self.bestsellers, labels, values, horizontal=True, color=Theme.CYAN)
            self.bestsellers.ax.set_xlabel("Units sold")
        self.bestsellers.draw()
