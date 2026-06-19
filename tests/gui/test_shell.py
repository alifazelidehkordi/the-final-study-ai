from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt

from gui.i18n import apply_locale
from gui.layout import LayoutState
from gui.navigation import NavDestination
from gui.pipeline.adapter import PipelineCommand
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


def test_history_resume_starts_pipeline_controller(
    qtbot,
    qapp,
    tmp_path: Path,
    monkeypatch,
) -> None:
    window = MainShell(LIGHT_COLORS)
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)
    manifest = tmp_path / "run.json"
    command = PipelineCommand(
        run_id="resume-run",
        argv=("python", "run_pipeline.py", "--resume", str(manifest)),
        work_dir=tmp_path / "work",
        event_file=tmp_path / "events.jsonl",
        manifest_file=manifest,
        log_file=tmp_path / "run.log",
        stop_file=tmp_path / "stop.requested",
    )
    started: list[PipelineCommand] = []
    monkeypatch.setattr(
        "gui.pipeline.contracts_bridge.load_run_manifest",
        lambda _path: {"status": "failed"},
    )
    monkeypatch.setattr(
        "gui.pipeline.resume_adapter.build_resume_command",
        lambda _path: command,
    )
    monkeypatch.setattr(window._pipeline_controller, "start", started.append)

    window._resume_from_manifest(manifest)

    assert started == [command]
    assert window._pages[NavDestination.PROGRESS].isVisible()
