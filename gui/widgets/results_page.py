"""Validated artifact results for a completed or partial run."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gui.pipeline.artifact_catalog import ArtifactEntry, catalog_run_artifacts
from gui.pipeline.run_store import RunSummary, load_run_summary
from gui.platform.open_path import open_folder, open_path
from gui.tokens import SPACING, ColorTokens
from gui.widgets.path_label import PathLabel


class ResultsPage(QWidget):
    def __init__(self, colors: ColorTokens, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._colors = colors
        self._summary: RunSummary | None = None
        self.setObjectName("resultsPage")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl)
        layout.setSpacing(SPACING.md)

        self._title = QLabel(self)
        self._subtitle = QLabel(self)
        self._subtitle.setWordWrap(True)
        self._status = QLabel(self)
        self._work_dir = PathLabel("", self)
        self._artifacts = QListWidget(self)
        self._detail = QLabel(self)
        self._detail.setWordWrap(True)

        action_row = QHBoxLayout()
        self._open_button = QPushButton(self)
        self._open_button.clicked.connect(self._open_selected)
        self._folder_button = QPushButton(self)
        self._folder_button.clicked.connect(self._open_work_dir)
        action_row.addWidget(self._open_button)
        action_row.addWidget(self._folder_button)
        action_row.addStretch(1)

        layout.addWidget(self._title)
        layout.addWidget(self._subtitle)
        layout.addWidget(self._status)
        layout.addWidget(self._work_dir)
        layout.addWidget(self._artifacts, stretch=1)
        layout.addWidget(self._detail)
        layout.addLayout(action_row)

        self._artifacts.currentItemChanged.connect(self._show_selected_detail)
        self.refresh_style()
        self.retranslate_ui()

    def set_colors(self, colors: ColorTokens) -> None:
        self._colors = colors
        self.refresh_style()

    def retranslate_ui(self) -> None:
        self._title.setText(self.tr("Results"))
        self._subtitle.setText(
            self.tr("Open validated Markdown, index, OPML, and XMind outputs.")
        )
        self._open_button.setText(self.tr("Open"))
        self._folder_button.setText(self.tr("Open work folder"))
        if self._summary is None:
            self._status.setText(self.tr("Select a run from History to inspect outputs."))

    def refresh_style(self) -> None:
        colors = self._colors
        self._title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {colors.text};")
        self._subtitle.setStyleSheet(f"color: {colors.text_muted};")
        self._detail.setStyleSheet(f"color: {colors.text_muted};")

    def show_run(self, manifest_path: Path) -> None:
        self._summary = load_run_summary(manifest_path)
        self._work_dir.set_path(str(self._summary.work_dir))
        status = self._summary.status.replace("_", " ")
        self._status.setText(f"{self.tr('Status')}: {status} · {self._summary.preset}")
        self._artifacts.clear()
        entries = catalog_run_artifacts(self._summary.work_dir, self._summary.manifest)
        for entry in entries:
            item = QListWidgetItem(self._format_entry(entry))
            item.setData(Qt.ItemDataRole.UserRole, entry)
            self._artifacts.addItem(item)
        if self._artifacts.count():
            self._artifacts.setCurrentRow(0)

    def _format_entry(self, entry: ArtifactEntry) -> str:
        flags: list[str] = []
        if not entry.valid:
            flags.append(self.tr("invalid"))
        if entry.changed:
            flags.append(self.tr("changed"))
        suffix = f" ({', '.join(flags)})" if flags else ""
        return f"{entry.label}{suffix}"

    def _show_selected_detail(self) -> None:
        item = self._artifacts.currentItem()
        if item is None:
            self._detail.setText("")
            return
        entry = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(entry, ArtifactEntry):
            self._detail.setText("")
            return
        lines = [str(entry.path)]
        if entry.detail:
            lines.append(entry.detail)
        if entry.changed:
            lines.append(self.tr("Recorded artifact hash no longer matches disk."))
        self._detail.setText("\n".join(lines))

    def _open_selected(self) -> None:
        item = self._artifacts.currentItem()
        if item is None:
            return
        entry = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(entry, ArtifactEntry):
            open_path(entry.path)

    def _open_work_dir(self) -> None:
        if self._summary is None:
            return
        open_folder(self._summary.work_dir)