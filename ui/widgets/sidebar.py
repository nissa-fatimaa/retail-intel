from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from config.settings import APP_NAME, ROLE_LABELS, Theme
from ui.widgets.logo_widget import LogoWidget


@dataclass
class NavItem:
    key: str
    label: str
    icon_glyph: str  #short text icon (avoiding emojis and using simple shapes)


class Sidebar(QFrame):
    nav_selected = pyqtSignal(str)
    logout_clicked = pyqtSignal()

    def __init__(self, *, items: list[NavItem], user_full_name: str, role: str,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(240)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        self._items = items
        self._buttons: dict[str, QPushButton] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 22, 18, 18)
        layout.setSpacing(6)

        # Brand
        brand = LogoWidget(size=34, show_name=True)
        layout.addWidget(brand)
        layout.addSpacing(18)

        # Section label
        section = QLabel("NAVIGATION")
        section.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 10px; font-weight: 600; "
            "letter-spacing: 1.4px; padding-left: 8px;"
        )
        layout.addWidget(section)
        layout.addSpacing(6)

        #nav items
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        for item in items:
            btn = QPushButton(f"  {item.icon_glyph}    {item.label}")
            btn.setObjectName("navItem")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _checked, k=item.key: self.nav_selected.emit(k))
            self._buttons[item.key] = btn
            self.button_group.addButton(btn)
            layout.addWidget(btn)

        layout.addStretch(1)

        #footer (user card and sign out)
        layout.addWidget(self._make_user_card(user_full_name, role))

        logout_btn = QPushButton("Sign out")
        logout_btn.setProperty("ghost", True)
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.clicked.connect(self.logout_clicked.emit)
        layout.addWidget(logout_btn)

        #select first by default
        if items:
            self._buttons[items[0].key].setChecked(True)

    def _make_user_card(self, full_name: str, role: str) -> QFrame:
        card = QFrame()
        card.setObjectName("cardElevated")
        card.setMinimumHeight(64)
        h = QHBoxLayout(card)
        h.setContentsMargins(12, 10, 12, 10)
        h.setSpacing(10)

        initials = "".join(p[0] for p in full_name.split()[:2]).upper() or "U"
        avatar = QLabel(initials)
        avatar.setFixedSize(36, 36)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(
            f"background-color: {Theme.ACCENT}; color: white; border-radius: 18px; "
            f"font-weight: 700; font-size: 13px;"
        )
        h.addWidget(avatar)

        text = QVBoxLayout()
        text.setSpacing(0)
        name = QLabel(full_name)
        name.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-weight: 600; font-size: 12px;")
        role_label = QLabel(ROLE_LABELS.get(role, role))
        role_label.setStyleSheet(f"color: {Theme.CYAN}; font-size: 10.5px; font-weight: 500;")
        text.addWidget(name)
        text.addWidget(role_label)
        wrap = QWidget()
        wrap.setLayout(text)
        h.addWidget(wrap, 1)
        return card

    def select(self, key: str) -> None:
        if key in self._buttons:
            self._buttons[key].setChecked(True)
            self.nav_selected.emit(key)
