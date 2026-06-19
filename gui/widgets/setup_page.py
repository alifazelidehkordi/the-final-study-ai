"""Setup screen for dependency health and login probing."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QProcess, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gui.dependencies.installer import run_confirmed_install_command
from gui.dependencies.models import DependencyHealth, DependencyReport, InstallPlan
from gui.dependencies.registry import DependencyRegistry
from gui.paths import browser_profile_dir
from gui.settings import AppSettings
from gui.tokens import SPACING, ColorTokens
from gui.widgets.install_dialog import InstallConfirmDialog

_HEALTH_COLORS = {
    DependencyHealth.READY: "#1f8f5f",
    DependencyHealth.MISSING: "#b42318",
    DependencyHealth.UNSUPPORTED: "#b42318",
    DependencyHealth.REPAIRABLE: "#b54708",
    DependencyHealth.CHECKING: "#5b6472",
    DependencyHealth.UNKNOWN: "#5b6472",
}


class SetupPage(QWidget):
    def __init__(self, colors: ColorTokens, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._colors = colors
        self._settings = AppSettings.load()
        self._registry = DependencyRegistry(settings=self._settings)
        self._probe_process: QProcess | None = None
        self.setObjectName("setupPage")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl)
        layout.setSpacing(SPACING.md)

        self._title = QLabel(self)
        self._title.setObjectName("setupTitle")
        self._subtitle = QLabel(self)
        self._subtitle.setWordWrap(True)
        layout.addWidget(self._title)
        layout.addWidget(self._subtitle)

        actions = QHBoxLayout()
        self._refresh_button = QPushButton(self)
        self._refresh_button.clicked.connect(self.refresh_reports)
        self._login_button = QPushButton(self)
        self._login_button.clicked.connect(self.start_login_probe)
        actions.addWidget(self._refresh_button)
        actions.addWidget(self._login_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        self._list = QListWidget(self)
        self._list.setObjectName("dependencyList")
        layout.addWidget(self._list, stretch=1)

        self._detail = QLabel(self)
        self._detail.setWordWrap(True)
        self._detail.setObjectName("dependencyDetail")
        layout.addWidget(self._detail)

        action_row = QHBoxLayout()
        self._install_button = QPushButton(self)
        self._install_button.setEnabled(False)
        self._install_button.clicked.connect(self.confirm_install_plan)
        action_row.addWidget(self._install_button)
        action_row.addStretch(1)
        layout.addLayout(action_row)

        self._list.currentItemChanged.connect(self._show_selected_report)
        self.refresh_style()
        self.retranslate_ui()
        self.refresh_reports()

    def set_colors(self, colors: ColorTokens) -> None:
        self._colors = colors
        self.refresh_style()

    def refresh_style(self) -> None:
        colors = self._colors
        self._title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {colors.text};")
        self._subtitle.setStyleSheet(f"color: {colors.text_muted};")
        self._detail.setStyleSheet(f"color: {colors.text_muted};")
        self.setStyleSheet(
            f"""
            QListWidget {{
                background: {colors.surface};
                border: 1px solid {colors.border};
                border-radius: 12px;
            }}
            """
        )

    def retranslate_ui(self) -> None:
        self._title.setText(self.tr("Dependency Setup"))
        self._subtitle.setText(
            self.tr(
                "Review required tools before starting a pipeline run. "
                "Install actions always require explicit confirmation."
            )
        )
        self._refresh_button.setText(self.tr("Refresh checks"))
        self._login_button.setText(self.tr("Run visible login probe"))
        self._install_button.setText(self.tr("Review install plan"))

    def refresh_reports(self) -> None:
        self._registry = DependencyRegistry(settings=self._settings)
        self._list.clear()
        for report in self._registry.scan_all():
            item = QListWidgetItem(f"{report.title} — {report.health.value}")
            item.setData(Qt.ItemDataRole.UserRole, report)
            color = _HEALTH_COLORS.get(report.health, self._colors.text_muted)
            item.setForeground(QColor(color))
            self._list.addItem(item)
        if self._list.count():
            self._list.setCurrentRow(0)

    def _show_selected_report(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        if current is None:
            self._detail.setText("")
            self._install_button.setEnabled(False)
            return
        report: DependencyReport = current.data(Qt.ItemDataRole.UserRole)
        parts = [report.purpose]
        if report.detected_version:
            parts.append(f"Version: {report.detected_version}")
        if report.detected_path:
            parts.append(f"Path: {report.detected_path}")
        if report.detail:
            parts.append(report.detail)
        self._detail.setText("\n".join(parts))
        self._install_button.setEnabled(report.install_plan is not None)

    def confirm_install_plan(self) -> None:
        item = self._list.currentItem()
        if item is None:
            return
        report: DependencyReport = item.data(Qt.ItemDataRole.UserRole)
        if report.install_plan is None:
            return
        dialog = InstallConfirmDialog(report.install_plan, self._colors, self)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        self._run_install_plan(report.install_plan)

    def _run_install_plan(self, plan: InstallPlan) -> None:
        for command in plan.planned_commands:
            if plan.requires_privilege:
                continue
            run_confirmed_install_command(command, self)

    def start_login_probe(self) -> None:
        if self._probe_process is not None and self._probe_process.state() != QProcess.ProcessState.NotRunning:
            return
        script = Path(__file__).resolve().parents[2] / "scripts" / "chatgpt_login_probe.py"
        process = QProcess(self)
        process.setProgram(sys.executable)
        process.setArguments(
            [
                str(script),
                "--profile-dir",
                str(browser_profile_dir()),
                "--mindmap-project",
                str(self._registry.tool_paths.mindmap_project),
            ]
        )
        process.finished.connect(self._login_probe_finished)
        self._probe_process = process
        self._login_button.setEnabled(False)
        process.start()

    def _login_probe_finished(self, exit_code: int, _status: QProcess.ExitStatus) -> None:
        self._login_button.setEnabled(True)
        if exit_code == 0:
            self._settings.last_login_probe_status = "ready"
        elif exit_code == 1:
            self._settings.last_login_probe_status = "needs_login"
        else:
            self._settings.last_login_probe_status = "unknown"
        self._settings.save()
        self.refresh_reports()