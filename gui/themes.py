"""Apply system, light, and dark palettes to the Qt application."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QStyleFactory

from gui.settings import ThemeMode
from gui.tokens import DARK_COLORS, LIGHT_COLORS, TYPOGRAPHY, ColorTokens


def resolve_palette(mode: ThemeMode, application: QApplication) -> ColorTokens:
    if mode == ThemeMode.LIGHT:
        return LIGHT_COLORS
    if mode == ThemeMode.DARK:
        return DARK_COLORS
    is_dark = application.styleHints().colorScheme() == Qt.ColorScheme.Dark
    return DARK_COLORS if is_dark else LIGHT_COLORS


def apply_theme(application: QApplication, mode: ThemeMode) -> ColorTokens:
    application.setStyle(QStyleFactory.create("Fusion"))
    colors = resolve_palette(mode, application)
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(colors.window))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(colors.text))
    palette.setColor(QPalette.ColorRole.Base, QColor(colors.surface))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(colors.surface_alt))
    palette.setColor(QPalette.ColorRole.Text, QColor(colors.text))
    palette.setColor(QPalette.ColorRole.Button, QColor(colors.surface))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors.text))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(colors.accent))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(colors.window))
    application.setPalette(palette)
    application.setStyleSheet(
        f"""
        QWidget {{
            font-family: "{TYPOGRAPHY.font_family}", "DejaVu Sans", sans-serif;
            font-size: {TYPOGRAPHY.body_px}px;
            color: {colors.text};
        }}
        QMainWindow {{
            background: {colors.window};
        }}
        """
    )
    return colors