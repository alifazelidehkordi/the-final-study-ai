"""Persistent GUI preferences."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import QSettings


class ThemeMode(str, Enum):
    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"


class LocaleCode(str, Enum):
    EN = "en"
    FA = "fa"


ORGANIZATION = "TheFinalStudyAI"
APPLICATION = "the-final-study-ai"


@dataclass
class AppSettings:
    locale: LocaleCode = LocaleCode.EN
    theme_mode: ThemeMode = ThemeMode.SYSTEM
    ui_scale: float = 1.0
    last_login_probe_status: str = "unknown"

    def save(self) -> None:
        store = QSettings(ORGANIZATION, APPLICATION)
        store.setValue("locale", self.locale.value)
        store.setValue("theme_mode", self.theme_mode.value)
        store.setValue("ui_scale", self.ui_scale)
        store.setValue("last_login_probe_status", self.last_login_probe_status)

    @classmethod
    def load(cls) -> AppSettings:
        store = QSettings(ORGANIZATION, APPLICATION)
        locale = LocaleCode(store.value("locale", LocaleCode.EN.value))
        theme = ThemeMode(store.value("theme_mode", ThemeMode.SYSTEM.value))
        raw_scale = store.value("ui_scale", 1.0)
        scale = float(raw_scale) if isinstance(raw_scale, (int, float, str)) else 1.0
        login_status = store.value("last_login_probe_status", "unknown")
        return cls(
            locale=locale,
            theme_mode=theme,
            ui_scale=scale,
            last_login_probe_status=str(login_status),
        )