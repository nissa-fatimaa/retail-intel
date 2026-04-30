from __future__ import annotations

from datetime import date, timedelta

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config.settings import ROLE_VISITOR, Theme
from services.events_service import EventsService
from ui.widgets.stat_card import StatCard


class EventsPage(QWidget):
    def __init__(self, role: str = ROLE_VISITOR) -> None:
        super().__init__()
        self.role = role
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(16)

        #kpis
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(14)
        self.kpi_total = StatCard("Tracked Events", "0")
        self.kpi_next = StatCard("Next Event", "—")
        self.kpi_impact = StatCard("Avg Impact (next 30d)", "×1.00", accent=Theme.CYAN)
        for c in (self.kpi_total, self.kpi_next, self.kpi_impact):
            kpi_row.addWidget(c, 1)
        outer.addLayout(kpi_row)

        #filters
        ctrl = QFrame()
        ctrl.setObjectName("card")
        ch = QHBoxLayout(ctrl)
        ch.setContentsMargins(20, 14, 20, 14)
        ch.setSpacing(12)

        ch.addWidget(self._field_label("Window"))
        self.window_combo = QComboBox()
        self.window_combo.addItem("Next 14 days", 14)
        self.window_combo.addItem("Next 30 days", 30)
        self.window_combo.addItem("Next 60 days", 60)
        self.window_combo.addItem("Next 90 days", 90)
        self.window_combo.currentIndexChanged.connect(self._refresh_table)
        ch.addWidget(self.window_combo)

        ch.addWidget(self._field_label("Category"))
        self.cat_combo = QComboBox()
        self.cat_combo.addItem("All categories", None)
        for c in ("religious", "national", "local", "weather", "custom"):
            self.cat_combo.addItem(c.capitalize(), c)
        self.cat_combo.currentIndexChanged.connect(self._refresh_table)
        ch.addWidget(self.cat_combo)

        ch.addStretch(1)
        outer.addWidget(ctrl)

        #table card
        card = QFrame()
        card.setObjectName("card")
        cv = QVBoxLayout(card)
        cv.setContentsMargins(20, 16, 20, 16)
        cv.setSpacing(10)

        title = QLabel("Upcoming events")
        title.setProperty("role", "sectionTitle")
        cv.addWidget(title)

        self.table = QTableWidget()
        if self.role == ROLE_VISITOR:
            headers = ["Date", "Day", "Event", "Type"]
        else:
            headers = ["Date", "Day", "Event", "Type", "Expected Attendance", "Impact ×", "Notes"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        for i in range(len(headers)):
            mode = QHeaderView.ResizeMode.Stretch if i in (2, len(headers) - 1) else QHeaderView.ResizeMode.ResizeToContents
            self.table.horizontalHeader().setSectionResizeMode(i, mode)
        cv.addWidget(self.table, 1)
        outer.addWidget(card, 1)

    def _field_label(self, text: str) -> QLabel:
        l = QLabel(text)
        l.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; font-weight: 600;")
        return l

    def refresh(self) -> None:
        self._refresh_table()

    def _refresh_table(self) -> None:
        days = int(self.window_combo.currentData() or 30)
        cat = self.cat_combo.currentData()
        events = EventsService.upcoming(days=days)
        if cat:
            events = [e for e in events if e.category == cat]

        #kpis
        self.kpi_total.set_value(str(len(events)))
        if events:
            ev = events[0]
            self.kpi_next.set_value(ev.name[:30] + ("…" if len(ev.name) > 30 else ""))
            self.kpi_next.set_delta(f"{ev.event_date} • {ev.category}")
            avg_impact = sum(e.impact_factor for e in events) / len(events)
            self.kpi_impact.set_value(f"×{avg_impact:.2f}")
        else:
            self.kpi_next.set_value("None")
            self.kpi_next.set_delta("Quiet ahead")
            self.kpi_impact.set_value("×1.00")

        #table
        self.table.setRowCount(0)
        for ev in events:
            r = self.table.rowCount()
            self.table.insertRow(r)
            from datetime import date as _d
            d = _d.fromisoformat(ev.event_date)
            self.table.setItem(r, 0, QTableWidgetItem(ev.event_date))
            self.table.setItem(r, 1, QTableWidgetItem(d.strftime("%A")))
            self.table.setItem(r, 2, QTableWidgetItem(ev.name))
            type_item = QTableWidgetItem(ev.category.capitalize())
            self.table.setItem(r, 3, type_item)
            if self.role != ROLE_VISITOR:
                self.table.setItem(r, 4, QTableWidgetItem(f"{ev.expected_attendance:,}"))
                impact = QTableWidgetItem(f"×{ev.impact_factor:.2f}")
                if ev.impact_factor >= 1.10:
                    impact.setForeground(QBrush(QColor(Theme.SUCCESS)))
                elif ev.impact_factor <= 0.95:
                    impact.setForeground(QBrush(QColor(Theme.WARNING)))
                self.table.setItem(r, 5, impact)
                self.table.setItem(r, 6, QTableWidgetItem(ev.notes or ""))
