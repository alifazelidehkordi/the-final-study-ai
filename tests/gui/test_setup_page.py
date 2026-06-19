from __future__ import annotations

from PySide6.QtCore import Qt

from gui.dependencies.models import DependencyHealth
from gui.tokens import LIGHT_COLORS
from gui.widgets.setup_page import SetupPage


def test_setup_page_lists_dependencies(qtbot, qapp) -> None:
    page = SetupPage(LIGHT_COLORS)
    qtbot.addWidget(page)
    page.show()
    qtbot.waitExposed(page)

    assert page._list.count() >= 8
    first = page._list.item(0)
    assert first is not None
    assert "—" in first.text()


def test_setup_page_enables_install_plan_for_missing_dependency(qtbot, qapp, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MINDMAP_PROJECT", str(tmp_path / "missing-mindmap"))
    page = SetupPage(LIGHT_COLORS)
    qtbot.addWidget(page)
    page.refresh_reports()

    for row in range(page._list.count()):
        page._list.setCurrentRow(row)
        item = page._list.currentItem()
        assert item is not None
        report = item.data(Qt.ItemDataRole.UserRole)
        if report.health in (DependencyHealth.MISSING, DependencyHealth.REPAIRABLE) and report.install_plan:
            assert page._install_button.isEnabled()
            return
    raise AssertionError("Expected at least one dependency with an install plan.")