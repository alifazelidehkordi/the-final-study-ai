"""Application bootstrap."""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from gui.i18n import apply_locale
from gui.settings import AppSettings, ThemeMode
from gui.themes import apply_theme
from gui.widgets.shell import MainShell


def create_application(argv: list[str] | None = None) -> QApplication:
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    application = QApplication(argv or sys.argv)
    application.setApplicationName("The Final Study AI")
    application.setOrganizationName("TheFinalStudyAI")
    return application


def run_app(argv: list[str] | None = None) -> int:
    application = create_application(argv)
    settings = AppSettings.load()
    colors = apply_theme(application, settings.theme_mode)
    apply_locale(application, settings.locale)
    if settings.ui_scale != 1.0:
        font = application.font()
        font.setPointSizeF(font.pointSizeF() * settings.ui_scale)
        application.setFont(font)

    window = MainShell(colors)
    window.show()
    return application.exec()


def resolved_theme_mode(settings: AppSettings, application: QApplication) -> ThemeMode:
    if settings.theme_mode != ThemeMode.SYSTEM:
        return settings.theme_mode
    return (
        ThemeMode.DARK
        if application.styleHints().colorScheme() == Qt.ColorScheme.Dark
        else ThemeMode.LIGHT
    )