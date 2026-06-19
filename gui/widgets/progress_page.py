"""Minimal progress screen wired to the active pipeline process."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gui.pipeline.process_controller import PipelineProcessController, PipelineRunState
from gui.tokens import SPACING, ColorTokens
from gui.widgets.path_label import PathLabel


class ProgressPage(QWidget):
    def __init__(
        self,
        colors: ColorTokens,
        controller: PipelineProcessController,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._colors = colors
        self._controller = controller
        self._state: PipelineRunState | None = None
        self.setObjectName("progressPage")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl)
        layout.setSpacing(SPACING.md)

        self._title = QLabel(self)
        self._subtitle = QLabel(self)
        self._subtitle.setWordWrap(True)
        self._status = QLabel(self)
        self._work_dir = PathLabel("", self)
        action_row = QHBoxLayout()
        self._stop_button = QPushButton(self)
        self._stop_button.clicked.connect(self._controller.stop_now)
        self._stop_button.setEnabled(False)
        action_row.addWidget(self._stop_button)
        action_row.addStretch(1)
        self._log = QPlainTextEdit(self)
        self._log.setReadOnly(True)
        self._log.setObjectName("progressLog")

        layout.addWidget(self._title)
        layout.addWidget(self._subtitle)
        layout.addWidget(self._status)
        layout.addWidget(self._work_dir)
        layout.addLayout(action_row)
        layout.addWidget(self._log, stretch=1)

        self._controller.run_started.connect(self._on_run_started)
        self._controller.output_line.connect(self._append_log_line)
        self._controller.run_finished.connect(self._on_run_finished)

        self.refresh_style()
        self.retranslate_ui()

    def set_colors(self, colors: ColorTokens) -> None:
        self._colors = colors
        self.refresh_style()

    def retranslate_ui(self) -> None:
        self._title.setText(self.tr("Run Progress"))
        self._subtitle.setText(
            self.tr("Track stage status, item counts, and recent pipeline activity.")
        )
        self._status.setText(self.tr("No active run."))
        self._stop_button.setText(self.tr("Stop Now"))

    def refresh_style(self) -> None:
        colors = self._colors
        self._title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {colors.text};")
        self._subtitle.setStyleSheet(f"color: {colors.text_muted};")
        self._status.setStyleSheet(f"color: {colors.text};")
        self._stop_button.setStyleSheet(
            f"""
            QPushButton {{
                background: {colors.danger};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 14px;
            }}
            QPushButton:disabled {{
                background: {colors.border};
            }}
            """
        )
        self._log.setStyleSheet(
            f"""
            #progressLog {{
                border: 1px solid {colors.border};
                border-radius: 8px;
                background: {colors.surface};
                color: {colors.text};
            }}
            """
        )

    def _on_run_started(self, state: PipelineRunState) -> None:
        self._state = state
        self._log.clear()
        self._status.setText(self.tr("Running pipeline…"))
        self._work_dir.set_path(str(state.work_dir))
        self._stop_button.setEnabled(True)

    def _append_log_line(self, line: str) -> None:
        self._log.appendPlainText(line)

    def _on_run_finished(self, exit_code: int, state: PipelineRunState | None) -> None:
        self._stop_button.setEnabled(False)
        if state is None:
            self._status.setText(self.tr("Run finished."))
            return
        message = self.tr("Run finished with exit code %1.").replace("%1", str(exit_code))
        self._status.setText(message)