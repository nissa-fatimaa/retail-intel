from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from config.settings import APP_NAME, ROLE_EXECUTIVE, ROLE_LABELS, ROLE_STAFF, ROLE_VISITOR, Theme
from models.user import User
from ui.pages.dashboard_executive import ExecutiveDashboard
from ui.pages.dashboard_staff import StaffDashboard
from ui.pages.dashboard_visitor import VisitorDashboard
from ui.pages.events_page import EventsPage
from ui.pages.forecasting_page import ForecastingPage
from ui.pages.inventory_page import InventoryPage
from ui.pages.pricing_history_page import PricingHistoryPage
from ui.pages.pricing_page import PricingPage
from ui.pages.what_if_page import WhatIfPage
from ui.widgets.notification import show_toast
from ui.widgets.sidebar import NavItem, Sidebar


def _nav_for_role(role: str) -> list[NavItem]:
    if role == ROLE_STAFF:
        return [
            NavItem("dashboard", "Dashboard", "▣"),
            NavItem("inventory", "Inventory", "▤"),
            NavItem("events", "Local Events", "◆"),
        ]
    if role == ROLE_VISITOR:
        return [
            NavItem("dashboard", "Store Today", "▣"),
            NavItem("events", "What's On", "◆"),
        ]
    return [
        NavItem("dashboard", "Executive Overview", "▣"),
        NavItem("forecasting", "Demand Forecast", "▲"),
        NavItem("pricing", "Dynamic Pricing", "$"),
        NavItem("pricing_history", "Pricing History", "◷"),
        NavItem("whatif", "What-If Simulator", "✦"),
        NavItem("inventory", "Inventory", "▤"),
        NavItem("events", "Local Events", "◆"),
    ]


class MainWindow(QMainWindow):
    logout_requested = pyqtSignal()

    def __init__(self, user: User) -> None:
        super().__init__()
        self.user = user
        self.setWindowTitle(f"{APP_NAME} — {ROLE_LABELS.get(user.role, user.role)}")
        self.setMinimumSize(1280, 800)
        self.resize(1480, 900)

        #main central layout
        central = QWidget()
        central.setStyleSheet(f"background-color: {Theme.BG_BASE};")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        items = _nav_for_role(user.role)
        self.sidebar = Sidebar(items=items, user_full_name=user.full_name, role=user.role)
        self.sidebar.nav_selected.connect(self.on_nav)
        self.sidebar.logout_clicked.connect(self.on_logout)
        root.addWidget(self.sidebar)

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)

        right.addWidget(self._make_topbar())

        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background-color: {Theme.BG_BASE};")
        right.addWidget(self.stack, 1)

        right_wrap = QWidget()
        right_wrap.setLayout(right)
        root.addWidget(right_wrap, 1)

        self.pages: dict[str, QWidget] = {}
        self._build_pages(items)

        if items:
            self.sidebar.select(items[0].key)

    def _make_topbar(self) -> QFrame:
        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(64)
        h = QHBoxLayout(topbar)
        h.setContentsMargins(28, 0, 28, 0)
        h.setSpacing(16)

        self.page_title = QLabel("Dashboard")
        self.page_title.setProperty("role", "title")
        h.addWidget(self.page_title)

        self.page_subtitle = QLabel("")
        self.page_subtitle.setProperty("role", "subtitle")
        self.page_subtitle.setStyleSheet(
            f"color: {Theme.TEXT_SECONDARY}; padding-left: 14px; "
            f"border-left: 1px solid {Theme.BORDER}; margin-left: 4px;"
        )
        h.addWidget(self.page_subtitle)
        h.addStretch(1)

        location = QLabel("Lahore, Pakistan")
        location.setProperty("role", "badge")
        h.addWidget(location)

        role_badge = QLabel(ROLE_LABELS.get(self.user.role, self.user.role))
        role_badge.setProperty("role", "badgeSuccess" if self.user.role == ROLE_EXECUTIVE else "badge")
        h.addWidget(role_badge)
        return topbar

    def _build_pages(self, items: list[NavItem]) -> None:
        keys = {i.key for i in items}

        if "dashboard" in keys:
            if self.user.role == ROLE_STAFF:
                page = StaffDashboard()
            elif self.user.role == ROLE_VISITOR:
                page = VisitorDashboard()
            else:
                page = ExecutiveDashboard()
            self._add_page("dashboard", page)

        if "forecasting" in keys:
            self._add_page("forecasting", ForecastingPage())
        if "pricing" in keys:
            self._add_page("pricing", PricingPage())
        if "pricing_history" in keys:
            self._add_page("pricing_history", PricingHistoryPage())
        if "whatif" in keys:
            self._add_page("whatif", WhatIfPage())
        if "inventory" in keys:
            self._add_page("inventory", InventoryPage(role=self.user.role))
        if "events" in keys:
            self._add_page("events", EventsPage(role=self.user.role))

    def _add_page(self, key: str, page: QWidget) -> None:
        self.pages[key] = page
        self.stack.addWidget(page)

    def on_nav(self, key: str) -> None:
        page = self.pages.get(key)
        if page is None:
            return
        self.stack.setCurrentWidget(page)

        if hasattr(page, "refresh"):
            try:
                page.refresh()
            except Exception:
                show_toast(self, "Could not refresh page data.", level="error")

        title, sub = self._titles_for(key)
        self.page_title.setText(title)
        self.page_subtitle.setText(sub)

    def _titles_for(self, key: str) -> tuple[str, str]:
        mapping = {
            "dashboard": {
                ROLE_STAFF: ("Staff Dashboard", "Inventory health, restock alerts & today's sales"),
                ROLE_VISITOR: ("Store Today", "What's fresh, what's in season, what's happening"),
                ROLE_EXECUTIVE: ("Executive Overview", "Revenue, margins, forecast & strategic signals"),
            },
            "inventory": ("Inventory", "Browse the full product catalogue and stock health"),
            "events": ("Local Events", f"Events shaping demand around our stores"),
            "forecasting": ("Demand Forecast", "Rule-based 7-day forecast per product"),
            "pricing": ("Dynamic Pricing", "Tension-driven recommendations with explanations"),
            "pricing_history": ("Pricing History", "Audit log of every price change with revert"),
            "whatif": ("What-If Simulator", "Tweak conditions and see instant impact"),
        }
        if key == "dashboard":
            t, s = mapping["dashboard"][self.user.role]
            return t, s
        m = mapping.get(key, (key.title(), ""))
        if isinstance(m, tuple):
            return m
        return key.title(), ""

    def on_logout(self) -> None:
        self.logout_requested.emit()

    def closeEvent(self, event: QCloseEvent) -> None:
        super().closeEvent(event)
