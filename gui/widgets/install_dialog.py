"""Confirmation sheet for dependency install and repair plans."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from gui.dependencies.models import InstallPlan
from gui.tokens import SPACING, ColorTokens


class InstallConfirmDialog(QDialog):
    def __init__(
        self,
        plan: InstallPlan,
        colors: ColorTokens,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._plan = plan
        self.setWindowTitle(self.tr("Confirm dependency action"))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl)
        layout.setSpacing(SPACING.md)

        title = QLabel(plan.title, self)
        title.setStyleSheet("font-size: 16px; font-weight: 600;")
        summary = QLabel(plan.summary, self)
        summary.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(summary)

        if plan.license_notice:
            license_label = QLabel(self.tr("License notice"), self)
            license_label.setStyleSheet("font-weight: 600;")
            license_body = QLabel(plan.license_notice, self)
            license_body.setWordWrap(True)
            layout.addWidget(license_label)
            layout.addWidget(license_body)

        commands = QTextEdit(self)
        commands.setReadOnly(True)
        commands.setPlainText("\n".join(plan.planned_commands))
        layout.addWidget(QLabel(self.tr("Planned commands"), self))
        layout.addWidget(commands)

        fallback = QLabel(plan.manual_fallback, self)
        fallback.setWordWrap(True)
        layout.addWidget(QLabel(self.tr("Manual fallback"), self))
        layout.addWidget(fallback)

        if plan.requires_privilege:
            warning = QLabel(
                self.tr("This action may require administrator approval from your operating system."),
                self,
            )
            warning.setWordWrap(True)
            warning.setStyleSheet(f"color: {colors.danger};")
            layout.addWidget(warning)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)