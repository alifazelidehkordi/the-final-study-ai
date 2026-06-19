"""Run progress screen driven by JSONL events and process output."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gui.pipeline.event_watcher import EventWatcher
from gui.pipeline.process_controller import PipelineProcessController, PipelineRunState
from gui.pipeline.progress_tracker import ProgressSnapshot, ProgressTracker
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
        self._event_watcher = EventWatcher(self)
        self.setObjectName("progressPage")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl)
        layout.setSpacing(SPACING.md)

        self._title = QLabel(self)
        self._subtitle = QLabel(self)
        self._subtitle.setWordWrap(True)
        self._work_dir = PathLabel("", self)

        metrics = QFrame(self)
        metrics.setObjectName("progressMetrics")
        metrics_layout = QGridLayout(metrics)
        metrics_layout.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        metrics_layout.setHorizontalSpacing(SPACING.lg)
        metrics_layout.setVerticalSpacing(SPACING.sm)
        self._stage_value = QLabel(metrics)
        self._operation_value = QLabel(metrics)
        self._items_value = QLabel(metrics)
        self._elapsed_value = QLabel(metrics)
        self._eta_value = QLabel(metrics)
        self._artifacts_value = QLabel(metrics)
        for row, (label_text, value_widget) in enumerate(
            (
                ("Stage", self._stage_value),
                ("Current operation", self._operation_value),
                ("Items", self._items_value),
                ("Elapsed", self._elapsed_value),
                ("Estimate", self._eta_value),
                ("Artifacts", self._artifacts_value),
            )
        ):
            label = QLabel(label_text, metrics)
            label.setStyleSheet("font-weight: 600;")
            value_widget.setWordWrap(True)
            metrics_layout.addWidget(label, row, 0)
            metrics_layout.addWidget(value_widget, row, 1)

        self._activity = QListWidget(self)
        self._activity.setObjectName("recentActivity")
        self._activity.setMaximumHeight(140)

        action_row = QHBoxLayout()
        self._stop_after_button = QPushButton(self)
        self._stop_after_button.clicked.connect(self._controller.request_cooperative_stop)
        self._stop_after_button.setEnabled(False)
        self._stop_button = QPushButton(self)
        self._stop_button.clicked.connect(self._controller.stop_now)
        self._stop_button.setEnabled(False)
        action_row.addWidget(self._stop_after_button)
        action_row.addWidget(self._stop_button)
        action_row.addStretch(1)

        self._log = QPlainTextEdit(self)
        self._log.setReadOnly(True)
        self._log.setObjectName("progressLog")

        layout.addWidget(self._title)
        layout.addWidget(self._subtitle)
        layout.addWidget(self._work_dir)
        layout.addWidget(metrics)
        layout.addWidget(self._activity)
        layout.addLayout(action_row)
        layout.addWidget(self._log, stretch=1)

        self._controller.run_started.connect(self._on_run_started)
        self._controller.output_line.connect(self._append_log_line)
        self._controller.run_finished.connect(self._on_run_finished)
        self._event_watcher.snapshot_updated.connect(self._apply_snapshot)

        self.refresh_style()
        self.retranslate_ui()

    def event_watcher(self) -> EventWatcher:
        return self._event_watcher

    def set_colors(self, colors: ColorTokens) -> None:
        self._colors = colors
        self.refresh_style()

    def retranslate_ui(self) -> None:
        self._title.setText(self.tr("Run Progress"))
        self._subtitle.setText(
            self.tr("Track stage status, item counts, and recent pipeline activity.")
        )
        self._stop_after_button.setText(self.tr("Stop After Current Item"))
        self._stop_button.setText(self.tr("Stop Now"))
        if self._state is None:
            self._apply_snapshot(self._event_watcher.tracker().snapshot())

    def refresh_style(self) -> None:
        colors = self._colors
        self._title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {colors.text};")
        self._subtitle.setStyleSheet(f"color: {colors.text_muted};")
        self._stage_value.setStyleSheet(f"color: {colors.text};")
        self._operation_value.setStyleSheet(f"color: {colors.text};")
        self._items_value.setStyleSheet(f"color: {colors.text};")
        self._elapsed_value.setStyleSheet(f"color: {colors.text};")
        self._eta_value.setStyleSheet(f"color: {colors.text_muted};")
        self._artifacts_value.setStyleSheet(f"color: {colors.text};")
        self.setStyleSheet(
            f"""
            #progressMetrics {{
                border: 1px solid {colors.border};
                border-radius: 12px;
                background: {colors.surface};
            }}
            #recentActivity {{
                border: 1px solid {colors.border};
                border-radius: 8px;
                background: {colors.surface_alt};
            }}
            """
        )
        stop_style = f"""
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
        self._stop_button.setStyleSheet(stop_style)
        self._stop_after_button.setStyleSheet(
            stop_style.replace(colors.danger, colors.text_muted)
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
        self._activity.clear()
        self._work_dir.set_path(str(state.work_dir))
        self._event_watcher.watch(state.event_file)
        self._stop_button.setEnabled(True)

    def _append_log_line(self, line: str) -> None:
        self._log.appendPlainText(line)

    def _on_run_finished(self, _exit_code: int, state: PipelineRunState | None) -> None:
        self._stop_button.setEnabled(False)
        self._stop_after_button.setEnabled(False)
        if state is not None:
            self._event_watcher.watch(state.event_file)
        self._apply_snapshot(self._event_watcher.tracker().snapshot())

    def _apply_snapshot(self, snapshot: ProgressSnapshot) -> None:
        if self._state is None and not snapshot.stage:
            self._stage_value.setText(self.tr("No active run."))
            self._operation_value.setText("—")
            self._items_value.setText("—")
            self._elapsed_value.setText("—")
            self._eta_value.setText("—")
            self._artifacts_value.setText("—")
            return
        self._stage_value.setText(snapshot.stage_label)
        self._operation_value.setText(snapshot.current_operation)
        if snapshot.item_total:
            self._items_value.setText(
                f"{snapshot.completed_items} / {snapshot.item_total}"
            )
        else:
            self._items_value.setText(str(snapshot.completed_items))
        self._elapsed_value.setText(ProgressTracker._format_duration(snapshot.elapsed_seconds))
        self._eta_value.setText(snapshot.eta_label)
        if snapshot.artifact_counts:
            parts = [
                f"{count} {kind}"
                for kind, count in sorted(snapshot.artifact_counts.items())
            ]
            self._artifacts_value.setText(", ".join(parts))
        else:
            self._artifacts_value.setText("—")
        self._activity.clear()
        for line in snapshot.recent_activity:
            self._activity.addItem(line)
        running = self._controller.is_running()
        self._stop_after_button.setEnabled(running and snapshot.in_mindmap_stage)