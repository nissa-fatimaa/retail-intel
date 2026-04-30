from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from config.settings import APP_NAME, APP_TAGLINE, ASSETS_DIR, Theme

#square SVG logo with 'Retail Intel' brand mark
class LogoWidget(QWidget):

    def __init__(
        self,
        *,
        size: int = 36,
        show_name: bool = True,
        show_tagline: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        #svg logo
        svg_path = Path(ASSETS_DIR) / "logo.svg"
        if svg_path.exists():
            self.svg = QSvgWidget(str(svg_path))
            self.svg.setFixedSize(QSize(size, size))
            self.svg.setStyleSheet("background: transparent;")
            layout.addWidget(self.svg, alignment=Qt.AlignmentFlag.AlignVCenter)
        else:  #pragma: no cover
            placeholder = QLabel("RI")
            placeholder.setFixedSize(QSize(size, size))
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet(
                "background:#3B82F6;color:white;border-radius:8px;font-weight:800;"
            )
            layout.addWidget(placeholder)

        if show_name:
            text_box = QVBoxLayout()
            text_box.setContentsMargins(0, 0, 0, 0)
            text_box.setSpacing(0)

            row = QHBoxLayout()
            row.setSpacing(2)
            row.setContentsMargins(0, 0, 0, 0)
            retail = QLabel("Retail")
            retail.setProperty("role", "appName")
            retail.setStyleSheet("background: transparent; color: white; font-size: 22px; font-weight: 700;")
            intel = QLabel(" Intel")
            intel.setProperty("role", "appNameAccent")
            intel.setStyleSheet(f"background: transparent; color: {Theme.ACCENT}; font-size: 22px; font-weight: 700;")
            row.addWidget(retail)
            row.addWidget(intel)
            wrapper = QWidget()
            wrapper.setStyleSheet("background: transparent;")
            wrapper.setLayout(row)
            text_box.addWidget(wrapper)

            if show_tagline:
                tagline = QLabel(APP_TAGLINE)
                tagline.setProperty("role", "loginTagline")
                text_box.addWidget(tagline)

            text_widget = QWidget()
            text_widget.setLayout(text_box)
            layout.addWidget(text_widget, alignment=Qt.AlignmentFlag.AlignVCenter)

        layout.addStretch(1)
