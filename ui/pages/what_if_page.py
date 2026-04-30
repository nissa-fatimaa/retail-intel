from __future__ import annotations

from datetime import date, timedelta

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from config.settings import Theme
from models.event import LocalEvent
from models.product import Product, ProductRepository
from services.forecasting_service import ForecastingService, ProductForecast
from services.pricing_service import PricingService
from services.weather_service import DayWeather
from ui.widgets.chart_widget import ChartFrame, plot_line, style_axes
from ui.widgets.notification import show_toast
from ui.widgets.stat_card import StatCard
from utils.helpers import fmt_int, fmt_money, fmt_pct


class WhatIfPage(QWidget):

    def __init__(self) -> None:
        super().__init__()
        self._products: list[Product] = []
        self._build()

    def _build(self) -> None:
        outer = QHBoxLayout(self)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(18)

        #ledt (controls)
        outer.addWidget(self._build_controls(), 2)

        #right (outputs with kpi and charts)
        right = QVBoxLayout()
        right.setSpacing(16)

        #kpi row
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(14)
        self.kpi_units = StatCard("Forecast Units (7d)", "0", accent=Theme.CYAN)
        self.kpi_revenue = StatCard("Forecast Revenue (7d)", "Rs 0")
        self.kpi_price = StatCard("Recommended Price", "Rs 0")
        self.kpi_change = StatCard("Δ vs current price", "0%")
        for c in (self.kpi_units, self.kpi_revenue, self.kpi_price, self.kpi_change):
            kpi_row.addWidget(c, 1)
        right.addLayout(kpi_row)

        #chart
        self.chart = ChartFrame("Scenario forecast — next 7 days", height=300)
        right.addWidget(self.chart, 1)

        #reasoning detail card
        reasoning = QFrame()
        reasoning.setObjectName("card")
        rv = QVBoxLayout(reasoning)
        rv.setContentsMargins(20, 16, 20, 16)
        rv.setSpacing(8)
        title = QLabel("Scenario explanation")
        title.setProperty("role", "sectionTitle")
        rv.addWidget(title)
        self.scenario_text = QLabel("Adjust the controls on the left to see live impact.")
        self.scenario_text.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 13px;")
        self.scenario_text.setWordWrap(True)
        rv.addWidget(self.scenario_text)
        right.addWidget(reasoning)

        wrap = QWidget()
        wrap.setLayout(right)
        outer.addWidget(wrap, 5)

    def _build_controls(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        v = QVBoxLayout(card)
        v.setContentsMargins(22, 20, 22, 20)
        v.setSpacing(16)

        title = QLabel("Scenario inputs")
        title.setProperty("role", "sectionTitle")
        v.addWidget(title)

        sub = QLabel("Drag the sliders to override weather, events and stock.")
        sub.setProperty("role", "muted")
        sub.setWordWrap(True)
        v.addWidget(sub)

        #product selector
        v.addWidget(self._field_label("Product"))
        self.product_combo = QComboBox()
        self.product_combo.currentIndexChanged.connect(self._recompute)
        v.addWidget(self.product_combo)

        #stock override
        v.addWidget(self._field_label("Stock on hand"))
        stock_row = QHBoxLayout()
        self.stock_slider = QSlider(Qt.Orientation.Horizontal)
        self.stock_slider.setRange(0, 500)
        self.stock_slider.setValue(50)
        self.stock_slider.valueChanged.connect(self._on_stock_changed)
        self.stock_value = QLabel("50")
        self.stock_value.setMinimumWidth(54)
        self.stock_value.setStyleSheet(f"color: {Theme.CYAN}; font-weight: 700;")
        stock_row.addWidget(self.stock_slider, 1)
        stock_row.addWidget(self.stock_value)
        srow_w = QWidget()
        srow_w.setLayout(stock_row)
        v.addWidget(srow_w)

        #temperature
        v.addWidget(self._field_label("Avg high temperature (°C)"))
        temp_row = QHBoxLayout()
        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setRange(5, 48)
        self.temp_slider.setValue(32)
        self.temp_slider.valueChanged.connect(self._on_temp_changed)
        self.temp_value = QLabel("32 °C")
        self.temp_value.setMinimumWidth(54)
        self.temp_value.setStyleSheet(f"color: {Theme.CYAN}; font-weight: 700;")
        temp_row.addWidget(self.temp_slider, 1)
        temp_row.addWidget(self.temp_value)
        trow_w = QWidget()
        trow_w.setLayout(temp_row)
        v.addWidget(trow_w)

        #rain
        v.addWidget(self._field_label("Daily rainfall (mm)"))
        rain_row = QHBoxLayout()
        self.rain_slider = QSlider(Qt.Orientation.Horizontal)
        self.rain_slider.setRange(0, 50)
        self.rain_slider.setValue(0)
        self.rain_slider.valueChanged.connect(self._on_rain_changed)
        self.rain_value = QLabel("0 mm")
        self.rain_value.setMinimumWidth(54)
        self.rain_value.setStyleSheet(f"color: {Theme.CYAN}; font-weight: 700;")
        rain_row.addWidget(self.rain_slider, 1)
        rain_row.addWidget(self.rain_value)
        rrow_w = QWidget()
        rrow_w.setLayout(rain_row)
        v.addWidget(rrow_w)

        #event impact
        v.addWidget(self._field_label("Local event impact (×)"))
        ev_row = QHBoxLayout()
        self.event_slider = QSlider(Qt.Orientation.Horizontal)
        self.event_slider.setRange(70, 150)   # represents 0.70 → 1.50
        self.event_slider.setValue(100)
        self.event_slider.valueChanged.connect(self._on_event_changed)
        self.event_value = QLabel("×1.00")
        self.event_value.setMinimumWidth(54)
        self.event_value.setStyleSheet(f"color: {Theme.CYAN}; font-weight: 700;")
        ev_row.addWidget(self.event_slider, 1)
        ev_row.addWidget(self.event_value)
        erow_w = QWidget()
        erow_w.setLayout(ev_row)
        v.addWidget(erow_w)

        v.addStretch(1)

        reset = QPushButton("Reset to current real-world values")
        reset.setProperty("ghost", True)
        reset.clicked.connect(self._reset_to_defaults)
        v.addWidget(reset)
        return card

    def _field_label(self, text: str) -> QLabel:
        l = QLabel(text)
        l.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; font-weight: 600;")
        return l

    #slider value handlers for uppdation and recomputation
    def _on_stock_changed(self, v: int) -> None:
        self.stock_value.setText(str(v))
        self._recompute()

    def _on_temp_changed(self, v: int) -> None:
        self.temp_value.setText(f"{v} °C")
        self._recompute()

    def _on_rain_changed(self, v: int) -> None:
        self.rain_value.setText(f"{v} mm")
        self._recompute()

    def _on_event_changed(self, v: int) -> None:
        self.event_value.setText(f"×{v / 100:.2f}")
        self._recompute()

    def refresh(self) -> None:
        self._products = ProductRepository.list_all()
        self.product_combo.blockSignals(True)
        self.product_combo.clear()
        for p in self._products:
            self.product_combo.addItem(f"{p.name}  ·  {p.category_name}", p.id)
        self.product_combo.blockSignals(False)
        if self._products:
            self._reset_to_defaults()

    def _selected_product(self) -> Product | None:
        if not self._products:
            return None
        pid = self.product_combo.currentData()
        return next((p for p in self._products if p.id == pid), self._products[0])

    def _reset_to_defaults(self) -> None:
        product = self._selected_product()
        if product:
            self.stock_slider.setValue(min(500, max(0, product.current_stock)))
        # lahore-typical defaults
        self.temp_slider.setValue(32)
        self.rain_slider.setValue(0)
        self.event_slider.setValue(100)
        self._recompute()

    def _recompute(self) -> None:
        product = self._selected_product()
        if product is None:
            return

        #override weather and event series
        from services.weather_service import _classify_condition

        temp_max = float(self.temp_slider.value())
        precip = float(self.rain_slider.value())
        condition = _classify_condition(temp_max, precip)
        event_factor = self.event_slider.value() / 100.0

        weather_overrides: dict[str, DayWeather] = {}
        events_overrides: dict[str, list[LocalEvent]] = {}
        today = date.today()
        for i in range(1, 8):
            d = today + timedelta(days=i)
            ds = d.isoformat()
            weather_overrides[ds] = DayWeather(
                record_date=ds,
                temp_max_c=temp_max,
                temp_min_c=max(0.0, temp_max - 8.0),
                precipitation_mm=precip,
                condition=condition,
                is_forecast=True,
            )
            if abs(event_factor - 1.0) > 0.001:
                events_overrides[ds] = [
                    LocalEvent(
                        id=-1,
                        name="Custom scenario event",
                        event_date=ds,
                        category="custom",
                        expected_attendance=0,
                        impact_factor=event_factor,
                        notes=None,
                    )
                ]

        #temporary product with overridden stock
        scenario_product = Product(
            id=product.id,
            sku=product.sku,
            name=product.name,
            category_id=product.category_id,
            category_name=product.category_name,
            unit=product.unit,
            cost_price=product.cost_price,
            msrp=product.msrp,
            current_price=product.current_price,
            current_stock=int(self.stock_slider.value()),
            safety_stock=product.safety_stock,
            weather_sensitivity=product.weather_sensitivity,
            is_active=product.is_active,
        )

        forecast = ForecastingService.forecast_product(
            scenario_product,
            horizon_days=7,
            weather_overrides=weather_overrides,
            events_overrides=events_overrides,
        )
        rec = PricingService.recommend(scenario_product, forecast=forecast)

        # KPIs
        self.kpi_units.set_value(fmt_int(forecast.total_units))
        self.kpi_revenue.set_value(fmt_money(forecast.total_units * rec.recommended_price))
        self.kpi_price.set_value(fmt_money(rec.recommended_price))
        delta_str = fmt_pct(rec.change_pct, signed=True)
        self.kpi_change.set_value(delta_str)
        if rec.change_pct > 0.5:
            self.kpi_change.value.setStyleSheet(f"color: {Theme.SUCCESS};")
        elif rec.change_pct < -0.5:
            self.kpi_change.value.setStyleSheet(f"color: {Theme.WARNING};")
        else:
            self.kpi_change.value.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")

        #chart
        labels = [d.forecast_date[5:] for d in forecast.days]
        values = [d.final for d in forecast.days]
        self.chart.clear()
        plot_line(self.chart, labels, values, color=Theme.CYAN, label=f"{product.name}")
        self.chart.ax.set_ylabel(f"Units / day ({product.unit})")
        self.chart.draw()

        #reasoning
        bits = []
        bits.append(
            f"<b>Scenario:</b> {temp_max:.0f}°C, {precip:.0f}mm rain, "
            f"event impact ×{event_factor:.2f}, stock {scenario_product.current_stock} {product.unit}."
        )
        bits.append(f"<b>Tension index:</b> {rec.tension_index:.2f} — {self._tension_summary(rec.tension_index)}")
        bits.append("")
        bits.append(rec.reason)
        self.scenario_text.setText("<br>".join(bits))

    def _tension_summary(self, tension: float) -> str:
        if tension >= 1.30:
            return "demand far exceeds stock — strong upward pricing signal."
        if tension >= 1.10:
            return "demand exceeds stock — modest upward pricing signal."
        if tension >= 0.90:
            return "supply and demand are balanced."
        if tension >= 0.70:
            return "demand softer than stock — consider a small price drop."
        return "demand much weaker than stock — discount strongly to clear inventory."
