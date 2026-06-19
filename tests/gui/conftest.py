from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from PySide6.QtWidgets import QApplication

from gui.settings import AppSettings, LocaleCode, ThemeMode
from gui.themes import apply_theme


@pytest.fixture(scope="session")
def qapp() -> Iterator[QApplication]:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ.setdefault("QT_SCALE_FACTOR", "1")
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    apply_theme(application, ThemeMode.LIGHT)
    yield application


@pytest.fixture
def english_settings() -> AppSettings:
    return AppSettings(locale=LocaleCode.EN, theme_mode=ThemeMode.LIGHT, ui_scale=1.0)


@pytest.fixture
def persian_settings() -> AppSettings:
    return AppSettings(locale=LocaleCode.FA, theme_mode=ThemeMode.LIGHT, ui_scale=1.0)