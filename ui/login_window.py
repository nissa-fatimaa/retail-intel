from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpacerItem,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from config.settings import (
    APP_NAME,
    APP_TAGLINE,
    DEFAULT_CITY,
    DEFAULT_COUNTRY,
    DEMO_ACCOUNTS,
    ROLE_DESCRIPTIONS,
    ROLE_LABELS,
    ROLES,
    Theme,
)
from models.user import User
from services.auth_service import AuthService
from ui.widgets.logo_widget import LogoWidget
from ui.widgets.notification import show_toast


class LoginWindow(QWidget):

    login_successful = pyqtSignal(object)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} - Sign In")
        self.setFixedSize(980, 620)
        self.setStyleSheet(
            f"QWidget {{ background-color: {Theme.BG_DEEP}; }}"
        )

        outer = QHBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(20)

        outer.addWidget(self._make_left_panel(), 5)
        outer.addWidget(self._make_right_panel(), 4)

    def _make_left_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("card")
        panel.setStyleSheet(
            f"""
            QFrame#card {{
                background-color: {Theme.BG_SURFACE};
                border: 1px solid {Theme.BORDER};
                border-radius: 18px;
            }}
            QLabel {{
                background: transparent;
            }}
            """
        )

        v = QVBoxLayout(panel)
        v.setContentsMargins(36, 36, 36, 36)
        v.setSpacing(0)

        brand = LogoWidget(size=46, show_name=True)
        v.addWidget(brand)
        v.addSpacing(28)

        hero = QLabel("Retail Intelligence,\ndecoded for everyone.")
        hero.setProperty("role", "loginHero")
        hero.setWordWrap(True)
        v.addWidget(hero)
        v.addSpacing(10)

        sub = QLabel(
            "Connect your sales data with weather, local events and "
            "transparent forecasting, without the black-box guesswork"
        )
        sub.setProperty("role", "loginTagline")
        sub.setWordWrap(True)
        v.addWidget(sub)
        v.addSpacing(28)

        section = QLabel("ROLES")
        section.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 14px; font-weight: 600; "
            "letter-spacing: 1.6px;"
        )
        v.addWidget(section)
        v.addSpacing(8)

        for role in ROLES:
            v.addWidget(self._make_role_chip(role))
            v.addSpacing(8)

        v.addStretch(1)

        footer = QLabel(f"📍 Default location: {DEFAULT_CITY}, {DEFAULT_COUNTRY}".replace("📍", "•"))
        footer.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 12px;")
        v.addWidget(footer)
        return panel

    def _make_role_chip(self, role: str) -> QFrame:
        chip = QFrame()
        chip.setObjectName("cardElevated")
        chip.setStyleSheet(
            f"""
            QFrame#cardElevated {{
                background-color: {Theme.BG_ELEVATED};
                border: 1px solid {Theme.BORDER};
                border-radius: 12px;
            }}
            """
        )
        h = QHBoxLayout(chip)
        h.setContentsMargins(14, 10, 14, 10)
        h.setSpacing(12)

        dot = QLabel()
        dot.setFixedSize(10, 10)
        dot.setStyleSheet(
            f"background-color: {Theme.CYAN}; border-radius: 5px;"
        )
        h.addWidget(dot)

        block = QVBoxLayout()
        block.setSpacing(2)
        title = QLabel(ROLE_LABELS.get(role, role))
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 13px; font-weight: 600; background: transparent;")
        desc = QLabel(ROLE_DESCRIPTIONS.get(role, ""))
        desc.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11.75px; background: transparent;")
        desc.setWordWrap(True)
        block.addWidget(title)
        block.addWidget(desc)
        wrap = QWidget()
        wrap.setLayout(block)
        wrap.setStyleSheet("background: transparent;")
        h.addWidget(wrap, 1)
        return chip

    def _make_right_panel(self) -> QWidget:
        glass = QFrame()
        glass.setObjectName("glass")

        shadow = QGraphicsDropShadowEffect(glass)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 12)
        shadow.setColor(QColor(0, 0, 0, 140))
        glass.setGraphicsEffect(shadow)

        outer = QVBoxLayout(glass)
        outer.setContentsMargins(34, 30, 34, 26)
        outer.setSpacing(16)

        self.title_label = QLabel("Welcome back!")
        self.title_label.setProperty("role", "loginHero")
        outer.addWidget(self.title_label)

        self.subtitle_label = QLabel("Sign in to your dashboard.")
        self.subtitle_label.setProperty("role", "loginTagline")
        outer.addWidget(self.subtitle_label)

        outer.addSpacing(6)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._make_login_form())
        self.stack.addWidget(self._make_register_form())
        outer.addWidget(self.stack, 1)

        bottom = QHBoxLayout()
        bottom.setSpacing(4)
        bottom.addStretch(1)
        self.toggle_hint = QLabel("New here?")
        self.toggle_hint.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        self.toggle_btn = QPushButton("Create an account")
        self.toggle_btn.setProperty("link", True)
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.clicked.connect(self._toggle_mode)
        bottom.addWidget(self.toggle_hint)
        bottom.addWidget(self.toggle_btn)
        bottom.addStretch(1)
        outer.addLayout(bottom)

        return glass

    def _make_login_form(self) -> QWidget:
        wrap = QWidget()
        v = QVBoxLayout(wrap)
        v.setContentsMargins(0, 6, 0, 0)
        v.setSpacing(12)

        v.addWidget(self._labeled("Username", self._build_input("username")))
        v.addWidget(self._labeled("Password", self._build_input("password", password=True)))

        sign_in = QPushButton("Sign in")
        sign_in.setProperty("primary", True)
        sign_in.setMinimumHeight(42)
        sign_in.setCursor(Qt.CursorShape.PointingHandCursor)
        sign_in.clicked.connect(self._handle_login)
        v.addSpacing(2)
        v.addWidget(sign_in)

        #demo acc helpers
        demo_box = QFrame()
        demo_box.setObjectName("cardElevated")
        demo_layout = QVBoxLayout(demo_box)
        demo_layout.setContentsMargins(14, 12, 14, 12)
        demo_layout.setSpacing(8)
        demo_title = QLabel("Quick demo accounts")
        demo_title.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 10.5px; font-weight: 700; letter-spacing: 1.2px;"
        )
        demo_layout.addWidget(demo_title)

        for acc in DEMO_ACCOUNTS:
            row = QHBoxLayout()
            row.setSpacing(8)
            label = QLabel(f"{ROLE_LABELS[acc['role']]}")
            label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 12px; font-weight: 500;")
            creds = QLabel(f"{acc['username']} / {acc['password']}")
            creds.setStyleSheet(
                f"color: {Theme.TEXT_SECONDARY}; font-size: 11.5px; "
                f"font-family: 'JetBrains Mono', 'Consolas', monospace;"
            )
            use_btn = QPushButton("Use")
            use_btn.setProperty("ghost", True)
            use_btn.setFixedWidth(60)
            use_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            use_btn.clicked.connect(lambda _c, a=acc: self._fill_demo(a))
            row.addWidget(label, 1)
            row.addWidget(creds, 0)
            row.addWidget(use_btn)
            wrap_row = QWidget()
            wrap_row.setLayout(row)
            demo_layout.addWidget(wrap_row)

        v.addSpacing(4)
        v.addWidget(demo_box)
        v.addStretch(1)
        return wrap

    def _make_register_form(self) -> QWidget:
        wrap = QWidget()
        v = QVBoxLayout(wrap)
        v.setContentsMargins(0, 6, 0, 0)
        v.setSpacing(10)

        v.addWidget(self._labeled("Full name", self._build_input("full_name")))
        v.addWidget(self._labeled("Username", self._build_input("reg_username")))
        v.addWidget(self._labeled("Email (optional)", self._build_input("email")))
        v.addWidget(self._labeled("Password", self._build_input("reg_password", password=True)))

        #role selector
        role_combo = QComboBox()
        for role in ROLES:
            role_combo.addItem(ROLE_LABELS[role], role)
        self._inputs["role"] = role_combo
        v.addWidget(self._labeled("Role", role_combo))

        sign_up = QPushButton("Create account")
        sign_up.setProperty("primary", True)
        sign_up.setMinimumHeight(42)
        sign_up.setCursor(Qt.CursorShape.PointingHandCursor)
        sign_up.clicked.connect(self._handle_register)
        v.addSpacing(4)
        v.addWidget(sign_up)
        v.addStretch(1)
        return wrap


    def _build_input(self, key: str, *, password: bool = False) -> QLineEdit:
        if not hasattr(self, "_inputs"):
            self._inputs: dict[str, QWidget] = {}
        edit = QLineEdit()
        edit.setMinimumHeight(40)
        if password:
            edit.setEchoMode(QLineEdit.EchoMode.Password)
        edit.returnPressed.connect(self._handle_login if self.stack_mode_is_login() else self._handle_register)
        self._inputs[key] = edit
        return edit

    def stack_mode_is_login(self) -> bool:
        return getattr(self, "stack", None) is None or self.stack.currentIndex() == 0

    def _labeled(self, label: str, field: QWidget) -> QWidget:
        wrap = QWidget()
        v = QVBoxLayout(wrap)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)
        lab = QLabel(label.upper())
        lab.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 10px; font-weight: 700; "
            "letter-spacing: 1.2px;"
        )
        v.addWidget(lab)
        v.addWidget(field)
        return wrap

    def _toggle_mode(self) -> None:
        if self.stack.currentIndex() == 0:
            self.stack.setCurrentIndex(1)
            self.title_label.setText("Create your account")
            self.subtitle_label.setText("Pick a role and you're in.")
            self.toggle_hint.setText("Already have an account?")
            self.toggle_btn.setText("Sign in instead")
        else:
            self.stack.setCurrentIndex(0)
            self.title_label.setText("Welcome back")
            self.subtitle_label.setText("Sign in to your dashboard.")
            self.toggle_hint.setText("New here?")
            self.toggle_btn.setText("Create an account")

    def _fill_demo(self, account: dict) -> None:
        self._inputs["username"].setText(account["username"])
        self._inputs["password"].setText(account["password"])
        self._inputs["password"].setFocus()

    def _handle_login(self) -> None:
        username = self._inputs["username"].text().strip()
        password = self._inputs["password"].text()
        result = AuthService.login(username, password)
        if not result.success:
            show_toast(self, result.message, level="error")
            return
        show_toast(self, result.message, level="success")
        self.login_successful.emit(result.user)

    def _handle_register(self) -> None:
        full_name = self._inputs["full_name"].text().strip()
        username = self._inputs["reg_username"].text().strip()
        email = self._inputs["email"].text().strip() or None
        password = self._inputs["reg_password"].text()
        role = self._inputs["role"].currentData()

        result = AuthService.register(
            username=username,
            password=password,
            role=role,
            full_name=full_name,
            email=email,
        )
        if not result.success:
            show_toast(self, result.message, level="error")
            return
        show_toast(self, "Account created. You're signed in.", level="success")
        self.login_successful.emit(result.user)
