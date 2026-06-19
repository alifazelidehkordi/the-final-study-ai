#!/usr/bin/env python3
"""Launch the GUI offscreen and exit quickly for CI smoke checks."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from gui.app import create_application
from gui.settings import AppSettings, LocaleCode, ThemeMode
from gui.themes import apply_theme
from gui.widgets.shell import MainShell


def main() -> int:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ.setdefault("QT_SCALE_FACTOR", "1")
    application = create_application([])
    settings = AppSettings(locale=LocaleCode.EN, theme_mode=ThemeMode.LIGHT, ui_scale=1.0)
    colors = apply_theme(application, settings.theme_mode)
    window = MainShell(colors)
    window.show()
    QTimer.singleShot(300, application.quit)
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())