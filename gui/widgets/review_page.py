"""Segmentation review gate for exit-code 20 runs."""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gui.pipeline.process_controller import PipelineProcessController
from gui.pipeline.resume_adapter import (
    adjust_granularity,
    build_approve_command,
    build_regenerate_command,
)
from gui.platform.open_path import open_path
from gui.tokens import SPACING, ColorTokens
from gui.widgets.path_label import PathLabel


class ReviewPage(QWidget):
    review_action_requested = Signal(object)

    def __init__(
        self,
        colors: ColorTokens,
        controller: PipelineProcessController,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._colors = colors
        self._controller = controller
        self._manifest_path: Path | None = None
        self._work_dir: Path | None = None
        self.setObjectName("reviewPage")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl)
        layout.setSpacing(SPACING.md)

        self._title = QLabel(self)
        self._subtitle = QLabel(self)
        self._subtitle.setWordWrap(True)
        self._work_dir_label = PathLabel("", self)
        self._impact = QLabel(self)
        self._impact.setWordWrap(True)
        self._parts = QListWidget(self)
        self._parts.setObjectName("reviewParts")

        preview_row = QHBoxLayout()
        self._open_preview_button = QPushButton(self)
        self._open_preview_button.clicked.connect(self._open_preview)
        self._open_index_button = QPushButton(self)
        self._open_index_button.clicked.connect(self._open_index)
        preview_row.addWidget(self._open_preview_button)
        preview_row.addWidget(self._open_index_button)
        preview_row.addStretch(1)

        action_row = QHBoxLayout()
        self._approve_button = QPushButton(self)
        self._approve_button.clicked.connect(self._approve)
        self._finer_button = QPushButton(self)
        self._finer_button.clicked.connect(lambda: self._regenerate(finer=True))
        self._coarser_button = QPushButton(self)
        self._coarser_button.clicked.connect(lambda: self._regenerate(finer=False))
        self._keep_button = QPushButton(self)
        self._keep_button.clicked.connect(self._keep_outputs)
        action_row.addWidget(self._approve_button)
        action_row.addWidget(self._finer_button)
        action_row.addWidget(self._coarser_button)
        action_row.addWidget(self._keep_button)
        action_row.addStretch(1)

        layout.addWidget(self._title)
        layout.addWidget(self._subtitle)
        layout.addWidget(self._work_dir_label)
        layout.addWidget(self._impact)
        layout.addLayout(preview_row)
        layout.addWidget(self._parts, stretch=1)
        layout.addLayout(action_row)

        self.refresh_style()
        self.retranslate_ui()
        self.hide()

    def set_colors(self, colors: ColorTokens) -> None:
        self._colors = colors
        self.refresh_style()

    def retranslate_ui(self) -> None:
        self._title.setText(self.tr("Segmentation Review"))
        self._subtitle.setText(
            self.tr("Inspect the generated parts and index before mind maps run.")
        )
        self._impact.setText(
            self.tr(
                "Regenerating segmentation replaces parts/, STUDY_INDEX files, "
                "and any downstream OPML/XMind outputs in this work directory."
            )
        )
        self._open_preview_button.setText(self.tr("Open preview"))
        self._open_index_button.setText(self.tr("Open index"))
        self._approve_button.setText(self.tr("Approve and continue"))
        self._finer_button.setText(self.tr("Regenerate finer"))
        self._coarser_button.setText(self.tr("Regenerate coarser"))
        self._keep_button.setText(self.tr("Keep outputs and stop"))

    def refresh_style(self) -> None:
        colors = self._colors
        self._title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {colors.text};")
        self._subtitle.setStyleSheet(f"color: {colors.text_muted};")
        self._impact.setStyleSheet(f"color: {colors.danger};")
        button_style = f"""
            QPushButton {{
                background: {colors.surface};
                border: 1px solid {colors.border};
                border-radius: 8px;
                padding: 8px 14px;
            }}
        """
        primary_style = f"""
            QPushButton {{
                background: {colors.accent};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 14px;
                font-weight: 600;
            }}
        """
        for button in (
            self._open_preview_button,
            self._open_index_button,
            self._finer_button,
            self._coarser_button,
            self._keep_button,
        ):
            button.setStyleSheet(button_style)
        self._approve_button.setStyleSheet(primary_style)

    def load_manifest(self, manifest_path: Path) -> None:
        self._manifest_path = manifest_path
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        paths = payload.get("paths", {})
        self._work_dir = Path(str(paths.get("work_dir", manifest_path.parent)))
        self._work_dir_label.set_path(str(self._work_dir))
        self._parts.clear()
        manifest_file = self._work_dir / "parts-manifest.json"
        if manifest_file.is_file():
            parts_manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
            for part in parts_manifest.get("parts", []):
                if not isinstance(part, dict):
                    continue
                title = str(part.get("title", "Part"))
                start_page = part.get("start_page")
                end_page = part.get("end_page")
                if isinstance(start_page, int) and isinstance(end_page, int):
                    label = f"{title} (pages {start_page}-{end_page})"
                else:
                    label = title
                self._parts.addItem(QListWidgetItem(label))
        self.show()

    def _open_preview(self) -> None:
        if self._work_dir is None:
            return
        open_path(self._work_dir / "SEGMENTATION_PREVIEW.md")

    def _open_index(self) -> None:
        if self._work_dir is None:
            return
        open_path(self._work_dir / "STUDY_INDEX.md")

    def _approve(self) -> None:
        if self._manifest_path is None or self._controller.is_running():
            return
        command = build_approve_command(self._manifest_path)
        self._controller.start(command)
        self.review_action_requested.emit(command)

    def _regenerate(self, *, finer: bool) -> None:
        if self._manifest_path is None or self._work_dir is None or self._controller.is_running():
            return
        manifest = json.loads(self._manifest_path.read_text(encoding="utf-8"))
        options = manifest.get("options", {})
        if isinstance(options, dict):
            current = str(options.get("granularity", "normal"))
        else:
            current = "normal"
        granularity = adjust_granularity(current, finer=finer)
        command = build_regenerate_command(self._manifest_path, granularity=granularity)
        self._controller.start(command)
        self.review_action_requested.emit(command)

    def _keep_outputs(self) -> None:
        self.review_action_requested.emit(None)