from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class StatCard(QFrame):
    """card showing label / value / optional delta"""

    def __init__(
        self,
        title: str,
        value: str,
        *,
        delta: str | None = None,
        accent: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumHeight(118)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)

        self.label = QLabel(title)
        self.label.setProperty("role", "kpiLabel")
        layout.addWidget(self.label)

        self.value = QLabel(value)
        self.value.setProperty("role", "kpiValue")
        if accent:
            self.value.setStyleSheet(f"color: {accent};")
        layout.addWidget(self.value)

        self.delta = QLabel(delta or "")
        self.delta.setProperty("role", "kpiDelta")
        self.delta.setVisible(bool(delta))
        layout.addWidget(self.delta)

        layout.addStretch(1)

    def set_value(self, value: str) -> None:
        self.value.setText(value)

    def set_delta(self, delta: str | None) -> None:
        self.delta.setText(delta or "")
        self.delta.setVisible(bool(delta))
