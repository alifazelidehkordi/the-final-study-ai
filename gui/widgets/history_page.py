"""Run history with detail view and native open actions."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gui.pipeline.run_store import RunSummary, list_runs
from gui.platform.open_path import open_folder
from gui.tokens import SPACING, ColorTokens
from gui.widgets.path_label import PathLabel

_RESUMABLE_STATUSES = {"stopped", "interrupted", "partial", "failed"}


class HistoryPage(QWidget):
    open_results_requested = Signal(object)
    resume_requested = Signal(object)

    def __init__(self, colors: ColorTokens, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._colors = colors
        self._selected: RunSummary | None = None
        self.setObjectName("historyPage")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl)
        layout.setSpacing(SPACING.md)

        header = QHBoxLayout()
        self._title = QLabel(self)
        self._refresh_button = QPushButton(self)
        self._refresh_button.clicked.connect(self.refresh_runs)
        header.addWidget(self._title)
        header.addStretch(1)
        header.addWidget(self._refresh_button)

        self._subtitle = QLabel(self)
        self._subtitle.setWordWrap(True)
        self._runs = QListWidget(self)
        self._detail = QLabel(self)
        self._detail.setWordWrap(True)
        self._source = PathLabel("", self)
        self._work_dir = PathLabel("", self)

        action_row = QHBoxLayout()
        self._results_button = QPushButton(self)
        self._results_button.clicked.connect(self._open_results)
        self._folder_button = QPushButton(self)
        self._folder_button.clicked.connect(self._open_folder)
        self._resume_button = QPushButton(self)
        self._resume_button.clicked.connect(self._resume_run)
        action_row.addWidget(self._results_button)
        action_row.addWidget(self._folder_button)
        action_row.addWidget(self._resume_button)
        action_row.addStretch(1)

        layout.addLayout(header)
        layout.addWidget(self._subtitle)
        layout.addWidget(self._runs, stretch=1)
        layout.addWidget(self._detail)
        layout.addWidget(self._source)
        layout.addWidget(self._work_dir)
        layout.addLayout(action_row)

        self._runs.currentItemChanged.connect(self._show_selected)
        self.refresh_style()
        self.retranslate_ui()
        self.refresh_runs()

    def set_colors(self, colors: ColorTokens) -> None:
        self._colors = colors
        self.refresh_style()

    def retranslate_ui(self) -> None:
        self._title.setText(self.tr("Run History"))
        self._subtitle.setText(
            self.tr("Review completed, stopped, and resumable runs.")
        )
        self._refresh_button.setText(self.tr("Refresh"))
        self._results_button.setText(self.tr("View results"))
        self._folder_button.setText(self.tr("Open work folder"))
        self._resume_button.setText(self.tr("Resume"))
        self._update_resume_button()

    def refresh_style(self) -> None:
        colors = self._colors
        self._title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {colors.text};")
        self._subtitle.setStyleSheet(f"color: {colors.text_muted};")
        self._detail.setStyleSheet(f"color: {colors.text_muted};")

    def refresh_runs(self) -> None:
        current_id = self._selected.run_id if self._selected else None
        self._runs.clear()
        selected_row = 0
        for index, summary in enumerate(list_runs()):
            label = f"{summary.updated_at} · {summary.status} · {summary.preset}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, summary)
            self._runs.addItem(item)
            if summary.run_id == current_id:
                selected_row = index
        if self._runs.count():
            self._runs.setCurrentRow(selected_row)

    def _show_selected(self) -> None:
        item = self._runs.currentItem()
        if item is None:
            self._selected = None
            self._detail.setText("")
            self._source.set_path("")
            self._work_dir.set_path("")
            self._update_resume_button()
            return
        summary = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(summary, RunSummary):
            return
        self._selected = summary
        self._detail.setText(
            f"{self.tr('Preset')}: {summary.preset}\n"
            f"{self.tr('Status')}: {summary.status}\n"
            f"{self.tr('Updated')}: {summary.updated_at}"
        )
        self._source.set_path(summary.source_label)
        self._work_dir.set_path(str(summary.work_dir))
        self._update_resume_button()

    def _update_resume_button(self) -> None:
        if self._selected is None:
            self._resume_button.setEnabled(False)
            self._resume_button.setToolTip(self.tr("Select a run first."))
            return
        if self._selected.status == "awaiting_review":
            self._resume_button.setEnabled(True)
            self._resume_button.setToolTip(self.tr("Open segmentation review."))
            return
        if self._selected.status in _RESUMABLE_STATUSES:
            self._resume_button.setEnabled(False)
            self._resume_button.setToolTip(
                self.tr("Manifest resume is not available in this build yet.")
            )
            return
        self._resume_button.setEnabled(False)
        self._resume_button.setToolTip("")

    def _open_results(self) -> None:
        if self._selected is None:
            return
        self.open_results_requested.emit(self._selected.manifest_path)

    def _open_folder(self) -> None:
        if self._selected is None:
            return
        open_folder(self._selected.work_dir)

    def _resume_run(self) -> None:
        if self._selected is None:
            return
        self.resume_requested.emit(self._selected.manifest_path)