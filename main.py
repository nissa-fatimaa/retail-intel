from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QFontDatabase, QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox

from config.settings import APP_NAME, APP_VERSION, ASSETS_DIR
from database.db_manager import DatabaseManager
from database.seed_data import seed_if_empty
from ui.login_window import LoginWindow
from ui.main_window import MainWindow
from ui.styles import APP_STYLESHEET
from utils.logger import get_logger

logger = get_logger(__name__)


class RetailIntelApp:

    def __init__(self) -> None:
        self.qapp = QApplication(sys.argv)
        self.qapp.setApplicationName(APP_NAME)
        self.qapp.setApplicationVersion(APP_VERSION)
        self.qapp.setStyle("Fusion")

        default_font = QFont("Segoe UI", 10)
        default_font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        self.qapp.setFont(default_font)

        self.qapp.setStyleSheet(APP_STYLESHEET)

        icon_path = Path(ASSETS_DIR) / "logo.svg"
        if icon_path.exists():
            self.qapp.setWindowIcon(QIcon(str(icon_path)))

        try:
            DatabaseManager.initialize()
            seed_if_empty()
        except Exception as exc:  #pragma: no cover (defensive)
            logger.exception("Database initialization failed")
            QMessageBox.critical(
                None,
                "Database Error",
                f"Failed to initialize database:\n{exc}",
            )
            sys.exit(1)

        self.login_window: LoginWindow | None = None
        self.main_window: MainWindow | None = None

    def run(self) -> int:
        self.show_login()
        return self.qapp.exec()

    def show_login(self) -> None:
        self.main_window = None
        self.login_window = LoginWindow()
        self.login_window.login_successful.connect(self.on_login_success)
        self.login_window.show()

    def on_login_success(self, user) -> None:
        if self.login_window is not None:
            self.login_window.close()
            self.login_window = None

        self.main_window = MainWindow(user)
        self.main_window.logout_requested.connect(self.on_logout)
        self.main_window.show()

    def on_logout(self) -> None:
        if self.main_window is not None:
            self.main_window.close()
            self.main_window = None
        self.show_login()


def main() -> None:
    app = RetailIntelApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
