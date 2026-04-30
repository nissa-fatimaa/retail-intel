from __future__ import annotations

from typing import Iterable

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QFrame, QSizePolicy, QVBoxLayout, QWidget

from config.settings import Theme
from ui.styles import configure_matplotlib

configure_matplotlib()


class ChartCanvas(FigureCanvasQTAgg):
    """a FigureCanvas with a fresh axes ready to use"""

    def __init__(self, *, width: float = 6.0, height: float = 3.6, dpi: int = 100) -> None:
        self.figure = Figure(figsize=(width, height), dpi=dpi, layout="constrained")
        super().__init__(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.setStyleSheet("background-color: transparent;")

    def clear(self) -> None:
        self.figure.clf()
        self.ax = self.figure.add_subplot(111)


class ChartFrame(QFrame):
    """card-styled container hosting a matplotlib canvas with title"""

    def __init__(
        self,
        title: str = "",
        *,
        height: int = 280,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumHeight(height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)

        if title:
            from PyQt6.QtWidgets import QLabel

            self.title_label = QLabel(title)
            self.title_label.setProperty("role", "sectionTitle")
            layout.addWidget(self.title_label)

        self.canvas = ChartCanvas()
        layout.addWidget(self.canvas, 1)

    @property
    def ax(self):
        return self.canvas.ax

    @property
    def figure(self):
        return self.canvas.figure

    def clear(self) -> None:
        self.canvas.clear()

    def draw(self) -> None:
        self.canvas.draw_idle()


#convenience plotters
def style_axes(ax) -> None:
    ax.tick_params(colors=Theme.TEXT_SECONDARY, length=0)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(Theme.BORDER)
    ax.grid(True, color=Theme.BORDER, linestyle="--", alpha=0.5)


def plot_line(frame: ChartFrame, x: Iterable, y: Iterable, *, color: str | None = None,
              label: str | None = None, fill: bool = True) -> None:
    color = color or Theme.ACCENT
    ax = frame.ax
    ax.plot(list(x), list(y), color=color, linewidth=2.2, label=label, marker="o",
            markersize=4, markerfacecolor=color, markeredgecolor=Theme.BG_SURFACE)
    if fill:
        ax.fill_between(list(x), list(y), alpha=0.18, color=color)
    style_axes(ax)
    if label:
        ax.legend(loc="best", frameon=False)


def plot_bar(frame: ChartFrame, labels: Iterable[str], values: Iterable[float], *,
             color: str | None = None, horizontal: bool = False) -> None:
    color = color or Theme.ACCENT
    ax = frame.ax
    if horizontal:
        ax.barh(list(labels), list(values), color=color, edgecolor="none")
        ax.invert_yaxis()
    else:
        ax.bar(list(labels), list(values), color=color, edgecolor="none", width=0.65)
    style_axes(ax)


def plot_grouped_bar(frame: ChartFrame, labels: list[str], values_a: list[float],
                     values_b: list[float], label_a: str, label_b: str,
                     color_a: str | None = None, color_b: str | None = None) -> None:
    import numpy as np

    color_a = color_a or Theme.ACCENT
    color_b = color_b or Theme.CYAN
    ax = frame.ax
    x = np.arange(len(labels))
    width = 0.36
    ax.bar(x - width / 2, values_a, width, label=label_a, color=color_a, edgecolor="none")
    ax.bar(x + width / 2, values_b, width, label=label_b, color=color_b, edgecolor="none")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.legend(loc="best", frameon=False)
    style_axes(ax)


def plot_donut(frame: ChartFrame, labels: list[str], values: list[float]) -> None:
    ax = frame.ax
    colors = Theme.CHART_PALETTE[: len(values)]
    wedges, _texts, autotexts = ax.pie(
        values,
        labels=None,
        colors=colors,
        wedgeprops={"width": 0.42, "edgecolor": Theme.BG_SURFACE, "linewidth": 2},
        autopct=lambda p: f"{p:.0f}%" if p >= 5 else "",
        pctdistance=0.78,
        startangle=90,
    )
    for at in autotexts:
        at.set_color(Theme.TEXT_PRIMARY)
        at.set_fontsize(9)
        at.set_weight("600")
    ax.legend(
        wedges, labels, loc="center left", bbox_to_anchor=(1.0, 0.5),
        frameon=False, fontsize=9,
    )
    ax.set_aspect("equal")
