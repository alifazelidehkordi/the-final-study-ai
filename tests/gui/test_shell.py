from __future__ import annotations

from PySide6.QtCore import Qt

from gui.i18n import apply_locale
from gui.layout import LayoutState
from gui.navigation import NavDestination
from gui.settings import LocaleCode
from gui.tokens import LIGHT_COLORS
from gui.widgets.shell import MainShell


def test_shell_reports_layout_state(qtbot, qapp) -> None:
    window = MainShell(LIGHT_COLORS)
    qtbot.addWidget(window)

    window.resize(1280, 760)
    qtbot.waitExposed(window)
    assert window.layout_state() == LayoutState.WIDE

    window.resize(1100, 760)
    qtbot.waitExposed(window)
    assert window.layout_state() == LayoutState.COMPACT

    window.setMinimumWidth(0)
    window.resize(960, 760)
    window._apply_layout_state(LayoutState.RECOVERY)
    qtbot.waitExposed(window)
    assert window.layout_state() == LayoutState.RECOVERY
    assert window.property("layoutState") == LayoutState.RECOVERY.value
    assert window._status.parent() is window._root


def test_persian_locale_applies_rtl_and_translations(qtbot, qapp) -> None:
    apply_locale(qapp, LocaleCode.FA)
    window = MainShell(LIGHT_COLORS)
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)

    assert qapp.layoutDirection() == Qt.LayoutDirection.RightToLeft
    new_run = window._navigation._buttons[NavDestination.NEW_RUN].text()
    assert new_run == "اجرای جدید"


def test_navigation_switches_workspace(qtbot, qapp) -> None:
    window = MainShell(LIGHT_COLORS)
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)

    window._navigation._buttons[NavDestination.RESULTS].click()
    assert window._pages[NavDestination.RESULTS].isVisible()
    assert not window._pages[NavDestination.NEW_RUN].isVisible()