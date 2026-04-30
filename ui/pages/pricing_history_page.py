from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config.settings import Theme
from models.pricing_history import PricingHistoryRepository, PricingRecord
from models.product import ProductRepository
from ui.widgets.notification import show_toast
from ui.widgets.stat_card import StatCard
from utils.helpers import fmt_money, fmt_pct


class PricingHistoryPage(QWidget):

    def __init__(self) -> None:
        super().__init__()
        self._records: list[PricingRecord] = []
        self._displayed: list[PricingRecord] = []
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(16)

        #kpi row
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(14)
        self.kpi_total = StatCard("Total Records", "0")
        self.kpi_applied = StatCard("Currently Applied", "0", accent=Theme.SUCCESS)
        self.kpi_reverted = StatCard("Reverted", "0", accent=Theme.WARNING)
        self.kpi_suggested = StatCard("Suggested Only", "0", accent=Theme.CYAN)
        for c in (self.kpi_total, self.kpi_applied, self.kpi_reverted, self.kpi_suggested):
            kpi_row.addWidget(c, 1)
        outer.addLayout(kpi_row)

        #filters bar
        ctrl = QFrame()
        ctrl.setObjectName("card")
        ch = QHBoxLayout(ctrl)
        ch.setContentsMargins(20, 14, 20, 14)
        ch.setSpacing(12)

        ch.addWidget(self._field_label("Search"))
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search by product name...")
        self.search.setMinimumWidth(220)
        self.search.textChanged.connect(self._refresh_table)
        ch.addWidget(self.search)

        ch.addWidget(self._field_label("Status"))
        self.status_combo = QComboBox()
        self.status_combo.addItem("All statuses", "all")
        self.status_combo.addItem("Applied (active)", "applied")
        self.status_combo.addItem("Reverted", "reverted")
        self.status_combo.addItem("Suggested only", "suggested")
        self.status_combo.currentIndexChanged.connect(self.refresh)
        ch.addWidget(self.status_combo)

        ch.addWidget(self._field_label("Direction"))
        self.dir_combo = QComboBox()
        self.dir_combo.addItems(["All", "Increases", "Decreases"])
        self.dir_combo.currentIndexChanged.connect(self._refresh_table)
        ch.addWidget(self.dir_combo)

        ch.addStretch(1)
        reload_btn = QPushButton("Reload")
        reload_btn.setProperty("ghost", True)
        reload_btn.clicked.connect(self.refresh)
        ch.addWidget(reload_btn)

        self.export_btn = QPushButton("Export CSV")
        self.export_btn.setProperty("primary", True)
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.clicked.connect(self._export_csv)
        ch.addWidget(self.export_btn)
        outer.addWidget(ctrl)

        #table card
        table_card = QFrame()
        table_card.setObjectName("card")
        tv = QVBoxLayout(table_card)
        tv.setContentsMargins(20, 16, 20, 16)
        tv.setSpacing(10)

        head = QLabel("Audit log")
        head.setProperty("role", "sectionTitle")
        tv.addWidget(head)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["When", "Product", "Category", "Old", "New", "Δ %", "Status", "Action"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self._update_reason_panel)

        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        tv.addWidget(self.table, 1)
        outer.addWidget(table_card, 5)

        #reasoned detail panel
        detail = QFrame()
        detail.setObjectName("cardElevated")
        dv = QVBoxLayout(detail)
        dv.setContentsMargins(20, 16, 20, 16)
        dv.setSpacing(8)

        title = QLabel("Selected change — full reasoning")
        title.setProperty("role", "sectionTitle")
        dv.addWidget(title)

        self.detail_meta = QLabel("Select a row to see details.")
        self.detail_meta.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px;")
        self.detail_meta.setWordWrap(True)
        dv.addWidget(self.detail_meta)

        self.detail_reason = QLabel("")
        self.detail_reason.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 13px;")
        self.detail_reason.setWordWrap(True)
        self.detail_reason.setAlignment(Qt.AlignmentFlag.AlignTop)
        dv.addWidget(self.detail_reason, 1)

        outer.addWidget(detail, 2)

    def _field_label(self, text: str) -> QLabel:
        l = QLabel(text)
        l.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; font-weight: 600;")
        return l

    def refresh(self) -> None:
        status = self.status_combo.currentData() or "all"
        self._records = PricingHistoryRepository.list_all(status=status, limit=500)

        summary = PricingHistoryRepository.summary()
        self.kpi_total.set_value(str(summary["total"]))
        self.kpi_applied.set_value(str(summary["applied"]))
        self.kpi_reverted.set_value(str(summary["reverted"]))
        self.kpi_suggested.set_value(str(summary["suggested"]))

        self._refresh_table()

    def _refresh_table(self) -> None:
        q = self.search.text().strip().lower()
        direction = self.dir_combo.currentText()

        rows = list(self._records)
        if q:
            rows = [r for r in rows if q in r.product_name.lower()]
        if direction == "Increases":
            rows = [r for r in rows if r.change_pct > 0]
        elif direction == "Decreases":
            rows = [r for r in rows if r.change_pct < 0]

        self._displayed = rows
        self.table.setRowCount(0)
        for rec in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)

            #prefer applied_at (or reverted_at) when present, otherwise recommended_at
            ts = rec.reverted_at or rec.applied_at or rec.recommended_at
            self.table.setItem(r, 0, QTableWidgetItem(_fmt_ts(ts)))

            self.table.setItem(r, 1, QTableWidgetItem(rec.product_name))
            self.table.setItem(r, 2, QTableWidgetItem(rec.category_name or ""))
            self.table.setItem(r, 3, QTableWidgetItem(fmt_money(rec.old_price)))
            self.table.setItem(r, 4, QTableWidgetItem(fmt_money(rec.new_price)))

            d_item = QTableWidgetItem(fmt_pct(rec.change_pct, signed=True))
            if rec.change_pct > 0.5:
                d_item.setForeground(QBrush(QColor(Theme.SUCCESS)))
            elif rec.change_pct < -0.5:
                d_item.setForeground(QBrush(QColor(Theme.WARNING)))
            self.table.setItem(r, 5, d_item)

            status_item = QTableWidgetItem(rec.status)
            color = {
                "Applied": Theme.SUCCESS,
                "Reverted": Theme.WARNING,
                "Suggested": Theme.CYAN,
            }.get(rec.status, Theme.TEXT_PRIMARY)
            status_item.setForeground(QBrush(QColor(color)))
            self.table.setItem(r, 6, status_item)

            container, btn = self._make_revert_widget(rec)
            self.table.setCellWidget(r, 7, container)

        if rows:
            self.table.selectRow(0)
        else:
            self.detail_meta.setText("No records match the current filters.")
            self.detail_reason.setText("")

    def _make_revert_widget(self, rec: PricingRecord) -> tuple[QWidget, QPushButton]:
        wrap = QWidget()
        h = QHBoxLayout(wrap)
        h.setContentsMargins(4, 2, 4, 2)
        h.setSpacing(0)
        btn = QPushButton("Revert" if rec.applied and not rec.reverted else "—")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if rec.applied and not rec.reverted:
            btn.setProperty("ghost", True)
            btn.clicked.connect(lambda _c, r=rec: self._revert(r))
        else:
            btn.setEnabled(False)
            btn.setProperty("ghost", True)
            btn.setStyleSheet(f"color: {Theme.TEXT_MUTED};")
        h.addWidget(btn)
        return wrap, btn

    def _update_reason_panel(self) -> None:
        idx = self.table.currentRow()
        if idx < 0 or idx >= len(self._displayed):
            return
        rec = self._displayed[idx]
        meta_bits = [
            f"<b>{rec.product_name}</b>",
            f"Recommended: {_fmt_ts(rec.recommended_at)}",
        ]
        if rec.applied_at:
            meta_bits.append(f"Applied: {_fmt_ts(rec.applied_at)}")
        if rec.reverted_at:
            meta_bits.append(f"Reverted: {_fmt_ts(rec.reverted_at)}")
        meta_bits.append(
            f"{fmt_money(rec.old_price)} → {fmt_money(rec.new_price)} "
            f"({fmt_pct(rec.change_pct, signed=True)})"
        )
        self.detail_meta.setText("  •  ".join(meta_bits))
        self.detail_reason.setText(rec.reason)

    def _revert(self, rec: PricingRecord) -> None:
        confirm = QMessageBox(self)
        confirm.setWindowTitle("Revert price change")
        confirm.setIcon(QMessageBox.Icon.Question)
        confirm.setText(
            f"Revert <b>{rec.product_name}</b> from "
            f"{fmt_money(rec.new_price)} back to {fmt_money(rec.old_price)}?"
        )
        confirm.setInformativeText(
            "The product price will be restored to its previous value and a "
            "revert record will be logged."
        )
        confirm.setStandardButtons(
            QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Yes
        )
        confirm.setDefaultButton(QMessageBox.StandardButton.Cancel)
        if confirm.exec() != QMessageBox.StandardButton.Yes:
            return

        #1. restore product price
        ProductRepository.update_price(rec.product_id, rec.old_price)
        #2. mark this record as reverted
        PricingHistoryRepository.mark_reverted(rec.id)
        #3. log a counter-record so the audit trail shows the revert as its own line
        new_record_id = PricingHistoryRepository.add_recommendation(
            product_id=rec.product_id,
            old_price=rec.new_price,
            new_price=rec.old_price,
            change_pct=(rec.old_price / rec.new_price - 1.0) * 100.0 if rec.new_price else 0.0,
            reason=(
                f"Manual revert of change #{rec.id} "
                f"({fmt_money(rec.new_price)} → {fmt_money(rec.old_price)}). "
                f"Original reason: {rec.reason}"
            ),
        )
        PricingHistoryRepository.mark_applied(new_record_id)

        show_toast(
            self,
            f"Reverted {rec.product_name} to {fmt_money(rec.old_price)}.",
            level="success",
        )
        self.refresh()

    def _export_csv(self) -> None:
        if not self._displayed:
            show_toast(self, "Nothing to export - no records match the filters.", level="error")
            return

        status = (self.status_combo.currentData() or "all")
        stamp = datetime.now().strftime("%Y%m%d_%H%M")
        default_name = f"pricing_history_{status}_{stamp}.csv"
        default_path = str(Path.home() / default_name)

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export pricing history",
            default_path,
            "CSV files (*.csv);;All files (*.*)",
        )
        if not path:
            return
        if not path.lower().endswith(".csv"):
            path = path + ".csv"

        try:
            written = self._write_csv(Path(path), self._displayed)
        except OSError as exc:
            QMessageBox.critical(
                self,
                "Export failed",
                f"Could not write the file:\n{exc}",
            )
            return

        show_toast(
            self,
            f"Exported {written} records to {Path(path).name}",
            level="success",
        )

    def _write_csv(self, path: Path, records: list[PricingRecord]) -> int:
        headers = [
            "id",
            "product_id",
            "product_name",
            "category",
            "old_price_pkr",
            "new_price_pkr",
            "change_pct",
            "status",
            "recommended_at",
            "applied_at",
            "reverted_at",
            "reason",
        ]
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(headers)
            for rec in records:
                writer.writerow(
                    [
                        rec.id,
                        rec.product_id,
                        rec.product_name,
                        rec.category_name or "",
                        f"{rec.old_price:.2f}",
                        f"{rec.new_price:.2f}",
                        f"{rec.change_pct:.2f}",
                        rec.status,
                        rec.recommended_at or "",
                        rec.applied_at or "",
                        rec.reverted_at or "",
                        rec.reason,
                    ]
                )
        return len(records)


def _fmt_ts(ts: str | None) -> str:
    if not ts:
        return "-"
    try:
        dt = datetime.fromisoformat(ts.replace("Z", ""))
        return dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return ts
