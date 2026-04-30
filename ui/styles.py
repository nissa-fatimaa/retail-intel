from __future__ import annotations

from config.settings import Theme

APP_STYLESHEET = f"""
QWidget {{
    background-color: {Theme.BG_BASE};
    color: {Theme.TEXT_PRIMARY};
    font-family: "Segoe UI", "Inter", "SF Pro Text", "Helvetica Neue", sans-serif;
    font-size: 13px;
}}
QMainWindow, QDialog {{
    background-color: {Theme.BG_DEEP};
}}

QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {Theme.BORDER_STRONG};
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {Theme.ACCENT};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 10px;
}}
QScrollBar::handle:horizontal {{
    background: {Theme.BORDER_STRONG};
    border-radius: 5px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {Theme.ACCENT};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

QFrame#card {{
    background-color: {Theme.BG_SURFACE};
    border: 1px solid {Theme.BORDER};
    border-radius: 14px;
}}
QFrame#cardElevated {{
    background-color: {Theme.BG_ELEVATED};
    border: 1px solid {Theme.BORDER_STRONG};
    border-radius: 14px;
}}
QFrame#glass {{
    background-color: rgba(15, 27, 51, 0.78);
    border: 1px solid rgba(59, 130, 246, 0.25);
    border-radius: 18px;
}}
QFrame#hairline {{
    background-color: {Theme.BORDER};
    max-height: 1px;
    min-height: 1px;
}}
QFrame#sidebar {{
    background-color: {Theme.BG_DEEP};
    border-right: 1px solid {Theme.BORDER};
}}
QFrame#topbar {{
    background-color: {Theme.BG_SURFACE};
    border-bottom: 1px solid {Theme.BORDER};
}}

QLabel {{
    background: transparent;
    color: {Theme.TEXT_PRIMARY};
}}
QLabel[role="title"] {{
    color: {Theme.TEXT_PRIMARY};
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -0.3px;
}}
QLabel[role="subtitle"] {{
    color: {Theme.TEXT_SECONDARY};
    font-size: 13px;
    font-weight: 400;
}}
QLabel[role="sectionTitle"] {{
    color: {Theme.TEXT_PRIMARY};
    font-size: 15px;
    font-weight: 600;
    letter-spacing: -0.1px;
}}
QLabel[role="kpiLabel"] {{
    color: {Theme.TEXT_SECONDARY};
    font-size: 12px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 1.2px;
}}
QLabel[role="kpiValue"] {{
    color: {Theme.TEXT_PRIMARY};
    font-size: 26px;
    font-weight: 700;
    letter-spacing: -0.5px;
}}
QLabel[role="kpiDelta"] {{
    color: {Theme.TEXT_SECONDARY};
    font-size: 12px;
    font-weight: 500;
}}
QLabel[role="muted"] {{
    color: {Theme.TEXT_MUTED};
    font-size: 12px;
}}
QLabel[role="badge"] {{
    background-color: {Theme.ACCENT_SOFT};
    color: {Theme.CYAN};
    border-radius: 10px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
}}
QLabel[role="badgeSuccess"] {{
    background-color: rgba(34, 197, 94, 0.15);
    color: {Theme.SUCCESS};
    border-radius: 10px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
}}
QLabel[role="badgeWarn"] {{
    background-color: rgba(245, 158, 11, 0.15);
    color: {Theme.WARNING};
    border-radius: 10px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
}}
QLabel[role="badgeDanger"] {{
    background-color: rgba(239, 68, 68, 0.15);
    color: {Theme.DANGER};
    border-radius: 10px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
}}
QLabel[role="appName"] {{
    color: {Theme.TEXT_PRIMARY};
    font-size: 22px;
    font-weight: 800;
    letter-spacing: -0.5px;
}}
QLabel[role="appNameAccent"] {{
    color: {Theme.CYAN};
    font-size: 22px;
    font-weight: 800;
    letter-spacing: -0.5px;
}}
QLabel[role="loginHero"] {{
    color: {Theme.TEXT_PRIMARY};
    font-size: 30px;
    font-weight: 700;
    letter-spacing: -0.6px;
}}
QLabel[role="loginTagline"] {{
    color: {Theme.TEXT_SECONDARY};
    font-size: 14px;
    font-weight: 400;
}}

QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {{
    background-color: {Theme.BG_ELEVATED};
    color: {Theme.TEXT_PRIMARY};
    border: 1px solid {Theme.BORDER};
    border-radius: 8px;
    padding: 8px 12px;
    selection-background-color: {Theme.ACCENT};
    selection-color: {Theme.TEXT_ON_ACCENT};
    min-height: 18px;
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus,
QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {{
    border: 1px solid {Theme.ACCENT};
}}
QLineEdit:disabled, QComboBox:disabled {{
    color: {Theme.TEXT_MUTED};
    background-color: {Theme.BG_SURFACE};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {Theme.TEXT_SECONDARY};
    margin-right: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {Theme.BG_ELEVATED};
    color: {Theme.TEXT_PRIMARY};
    border: 1px solid {Theme.BORDER_STRONG};
    border-radius: 8px;
    selection-background-color: {Theme.ACCENT_SOFT};
    selection-color: {Theme.TEXT_PRIMARY};
    padding: 4px;
}}

QPushButton {{
    background-color: {Theme.BG_ELEVATED};
    color: {Theme.TEXT_PRIMARY};
    border: 1px solid {Theme.BORDER_STRONG};
    border-radius: 8px;
    padding: 9px 18px;
    font-weight: 600;
    font-size: 13px;
}}
QPushButton:hover {{
    background-color: {Theme.BORDER_STRONG};
    border-color: {Theme.ACCENT};
}}
QPushButton:pressed {{
    background-color: {Theme.BORDER};
}}
QPushButton:disabled {{
    background-color: {Theme.BG_SURFACE};
    color: {Theme.TEXT_MUTED};
    border-color: {Theme.BORDER};
}}
QPushButton[primary="true"] {{
    background-color: {Theme.ACCENT};
    color: {Theme.TEXT_ON_ACCENT};
    border: 1px solid {Theme.ACCENT};
}}
QPushButton[primary="true"]:hover {{
    background-color: {Theme.ACCENT_HOVER};
    border-color: {Theme.ACCENT_HOVER};
}}
QPushButton[primary="true"]:pressed {{
    background-color: {Theme.ACCENT_PRESSED};
}}
QPushButton[ghost="true"] {{
    background-color: transparent;
    border: 1px solid {Theme.BORDER};
}}
QPushButton[ghost="true"]:hover {{
    background-color: {Theme.ACCENT_SOFT};
    border-color: {Theme.ACCENT};
    color: {Theme.CYAN};
}}
QPushButton[link="true"] {{
    background: transparent;
    border: none;
    color: {Theme.CYAN};
    padding: 4px 6px;
    text-align: left;
}}
QPushButton[link="true"]:hover {{
    color: {Theme.ACCENT_HOVER};
}}

QPushButton#navItem {{
    text-align: left;
    background-color: transparent;
    border: none;
    border-radius: 10px;
    padding: 11px 14px;
    color: {Theme.TEXT_SECONDARY};
    font-weight: 500;
    font-size: 13.5px;
}}
QPushButton#navItem:hover {{
    background-color: {Theme.BG_ELEVATED};
    color: {Theme.TEXT_PRIMARY};
}}
QPushButton#navItem:checked {{
    background-color: {Theme.ACCENT_SOFT};
    color: {Theme.CYAN};
    font-weight: 600;
}}

QTableWidget, QTableView {{
    background-color: {Theme.BG_SURFACE};
    color: {Theme.TEXT_PRIMARY};
    gridline-color: {Theme.BORDER};
    border: 1px solid {Theme.BORDER};
    border-radius: 10px;
    selection-background-color: {Theme.ACCENT_SOFT};
    selection-color: {Theme.TEXT_PRIMARY};
    alternate-background-color: {Theme.BG_ELEVATED};
}}
QTableWidget::item, QTableView::item {{
    padding: 8px 6px;
    border: none;
}}
QHeaderView::section {{
    background-color: {Theme.BG_ELEVATED};
    color: {Theme.TEXT_SECONDARY};
    border: none;
    border-right: 1px solid {Theme.BORDER};
    border-bottom: 1px solid {Theme.BORDER};
    padding: 9px 8px;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.6px;
}}
QTableCornerButton::section {{
    background-color: {Theme.BG_ELEVATED};
    border: none;
    border-right: 1px solid {Theme.BORDER};
    border-bottom: 1px solid {Theme.BORDER};
}}

QTabWidget::pane {{
    border: 1px solid {Theme.BORDER};
    border-radius: 10px;
    background-color: {Theme.BG_SURFACE};
    top: -1px;
}}
QTabBar::tab {{
    background-color: transparent;
    color: {Theme.TEXT_SECONDARY};
    padding: 9px 18px;
    border: 1px solid transparent;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 4px;
    font-weight: 500;
}}
QTabBar::tab:selected {{
    background-color: {Theme.BG_SURFACE};
    color: {Theme.TEXT_PRIMARY};
    border: 1px solid {Theme.BORDER};
    border-bottom: none;
}}
QTabBar::tab:hover:!selected {{
    color: {Theme.TEXT_PRIMARY};
}}

QSlider::groove:horizontal {{
    height: 6px;
    background: {Theme.BG_ELEVATED};
    border-radius: 3px;
}}
QSlider::sub-page:horizontal {{
    background: {Theme.ACCENT};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: {Theme.CYAN};
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
    border: 2px solid {Theme.BG_DEEP};
}}

QProgressBar {{
    background-color: {Theme.BG_ELEVATED};
    border: 1px solid {Theme.BORDER};
    border-radius: 6px;
    text-align: center;
    color: {Theme.TEXT_PRIMARY};
    height: 14px;
}}
QProgressBar::chunk {{
    background-color: {Theme.ACCENT};
    border-radius: 5px;
}}

QToolTip {{
    background-color: {Theme.BG_ELEVATED};
    color: {Theme.TEXT_PRIMARY};
    border: 1px solid {Theme.BORDER_STRONG};
    border-radius: 6px;
    padding: 6px 8px;
}}
QMenu {{
    background-color: {Theme.BG_ELEVATED};
    border: 1px solid {Theme.BORDER_STRONG};
    border-radius: 8px;
    padding: 6px;
}}
QMenu::item {{
    padding: 8px 16px;
    border-radius: 6px;
}}
QMenu::item:selected {{
    background-color: {Theme.ACCENT_SOFT};
    color: {Theme.CYAN};
}}

/* Notification toast */
QFrame#toast {{
    background-color: {Theme.BG_ELEVATED};
    border: 1px solid {Theme.BORDER_STRONG};
    border-radius: 12px;
}}
QFrame#toastSuccess {{
    background-color: rgba(34, 197, 94, 0.18);
    border: 1px solid {Theme.SUCCESS};
    border-radius: 12px;
}}
QFrame#toastError {{
    background-color: rgba(239, 68, 68, 0.18);
    border: 1px solid {Theme.DANGER};
    border-radius: 12px;
}}
QFrame#toastInfo {{
    background-color: rgba(59, 130, 246, 0.18);
    border: 1px solid {Theme.ACCENT};
    border-radius: 12px;
}}

QFormLayout > QLabel {{
    color: {Theme.TEXT_SECONDARY};
}}

QRadioButton {{
    color: {Theme.TEXT_PRIMARY};
    spacing: 8px;
    padding: 4px;
}}
QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border: 1.5px solid {Theme.BORDER_STRONG};
    border-radius: 8px;
    background-color: {Theme.BG_ELEVATED};
}}
QRadioButton::indicator:checked {{
    background-color: {Theme.ACCENT};
    border: 4px solid {Theme.BG_DEEP};
    border-radius: 8px;
    outline: 2px solid {Theme.ACCENT};
}}

QCheckBox {{
    color: {Theme.TEXT_PRIMARY};
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1.5px solid {Theme.BORDER_STRONG};
    border-radius: 4px;
    background-color: {Theme.BG_ELEVATED};
}}
QCheckBox::indicator:checked {{
    background-color: {Theme.ACCENT};
    border-color: {Theme.ACCENT};
}}
"""

def configure_matplotlib() -> None:
    import matplotlib as mpl

    mpl.rcParams.update({
        "figure.facecolor": Theme.BG_SURFACE,
        "axes.facecolor": Theme.BG_SURFACE,
        "axes.edgecolor": Theme.BORDER,
        "axes.labelcolor": Theme.TEXT_SECONDARY,
        "axes.titlecolor": Theme.TEXT_PRIMARY,
        "axes.titlesize": 12,
        "axes.titleweight": "600",
        "axes.labelsize": 10,
        "xtick.color": Theme.TEXT_SECONDARY,
        "ytick.color": Theme.TEXT_SECONDARY,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "grid.color": Theme.BORDER,
        "grid.linestyle": "--",
        "grid.alpha": 0.5,
        "text.color": Theme.TEXT_PRIMARY,
        "legend.facecolor": Theme.BG_ELEVATED,
        "legend.edgecolor": Theme.BORDER,
        "legend.labelcolor": Theme.TEXT_PRIMARY,
        "legend.fontsize": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.family": ["Segoe UI", "DejaVu Sans"],
        "savefig.facecolor": Theme.BG_SURFACE,
        "savefig.edgecolor": Theme.BG_SURFACE,
    })
