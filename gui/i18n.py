"""Load Qt translations and apply locale layout direction."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QLocale, Qt, QTranslator
from PySide6.QtWidgets import QApplication

from gui.settings import LocaleCode

TRANSLATIONS_DIR = Path(__file__).resolve().parent / "resources" / "translations"


def translation_file(locale: LocaleCode) -> Path:
    return TRANSLATIONS_DIR / f"app_{locale.value}.qm"


def apply_locale(application: QApplication, locale: LocaleCode) -> None:
    previous = _active_translator()
    if previous is not None:
        application.removeTranslator(previous)
    translator = QTranslator(application)
    if locale != LocaleCode.EN:
        qm_path = translation_file(locale)
        if qm_path.is_file():
            translator.load(str(qm_path))
            application.installTranslator(translator)
    _store_translator(application, translator)
    application.setLayoutDirection(
        Qt.LayoutDirection.RightToLeft
        if locale == LocaleCode.FA
        else Qt.LayoutDirection.LeftToRight
    )
    QLocale.setDefault(QLocale("fa_IR" if locale == LocaleCode.FA else "en_US"))


def _active_translator() -> QTranslator | None:
    app = QApplication.instance()
    if app is None:
        return None
    return getattr(app, "_final_study_translator", None)


def _store_translator(application: QApplication, translator: QTranslator) -> None:
    application._final_study_translator = translator  # type: ignore[attr-defined]