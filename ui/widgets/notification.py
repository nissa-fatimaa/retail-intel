from __future__ import annotations

from PyQt6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QTimer,
    Qt,
    pyqtSignal,
)
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QWidget,
)


class Toast(QFrame):
    """self-disposing notification overlay."""

    closed = pyqtSignal()

    LEVEL_STYLES = {
        "success": ("toastSuccess", "✓"),
        "error": ("toastError", "✕"),
        "info": ("toastInfo", "ⓘ"),
    }

    def __init__(self, parent: QWidget, message: str, level: str = "info") -> None:
        super().__init__(parent)
        object_name, glyph = self.LEVEL_STYLES.get(level, ("toast", "•"))
        self.setObjectName(object_name)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 18, 12)
        layout.setSpacing(10)

        icon = QLabel(glyph)
        icon.setStyleSheet("font-size: 16px; font-weight: 700;")
        layout.addWidget(icon)

        label = QLabel(message)
        label.setWordWrap(True)
        label.setStyleSheet("font-size: 13px; font-weight: 500;")
        layout.addWidget(label, 1)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 110))
        self.setGraphicsEffect(shadow)

        self.adjustSize()
        self._position()

        QTimer.singleShot(3500, self._dismiss)

    def _position(self) -> None:
        if self.parent() is None:
            return
        margin = 24
        parent_w = self.parent().width()
        x = parent_w - self.width() - margin
        y = margin
        self.move(QPoint(x, y))

    def _dismiss(self) -> None:
        anim = QPropertyAnimation(self, b"windowOpacity", self)
        anim.setDuration(220)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim.finished.connect(self.close)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)


def show_toast(parent: QWidget, message: str, *, level: str = "info") -> None:
    toast = Toast(parent, message, level)
    toast.show()
    toast.raise_()
