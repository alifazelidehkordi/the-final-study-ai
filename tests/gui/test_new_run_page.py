from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from gui.dependencies.models import DependencyHealth, DependencyId, DependencyReport
from gui.pipeline.models import RunPreset
from gui.pipeline.process_controller import PipelineProcessController
from gui.tokens import LIGHT_COLORS
from gui.widgets.new_run_page import NewRunPage


def test_new_run_page_disables_blocked_preset(qtbot, qapp, monkeypatch) -> None:
    controller = PipelineProcessController()
    page = NewRunPage(LIGHT_COLORS, controller)
    qtbot.addWidget(page)

    def fake_scan_all() -> list[DependencyReport]:
        return [
            DependencyReport(
                dependency_id=DependencyId.MINDMAP_PROJECT,
                title="Mind-map project",
                purpose="Automation",
                health=DependencyHealth.MISSING,
                blocks_presets=("complete", "mindmaps_only"),
            )
        ]

    monkeypatch.setattr(page._registry, "scan_all", fake_scan_all)
    monkeypatch.setattr(page._registry, "presets_blocked", lambda: {"complete", "mindmaps_only"})
    page.refresh_preset_availability()

    assert not page._preset_cards[RunPreset.COMPLETE].isEnabled()
    assert page._preset_cards[RunPreset.MARKDOWN_INDEX].isEnabled()
    assert page._preset == RunPreset.MARKDOWN_INDEX


def test_new_run_page_start_disabled_without_pdf(qtbot, qapp) -> None:
    controller = PipelineProcessController()
    page = NewRunPage(LIGHT_COLORS, controller)
    qtbot.addWidget(page)
    page.refresh_preset_availability()
    assert not page._start_button.isEnabled()


def test_new_run_page_enables_start_with_valid_pdf(qtbot, qapp, tmp_path: Path, monkeypatch) -> None:
    controller = PipelineProcessController()
    page = NewRunPage(LIGHT_COLORS, controller)
    qtbot.addWidget(page)
    monkeypatch.setattr(page._registry, "presets_blocked", lambda: set())
    monkeypatch.setattr(page._registry, "scan_all", lambda: [])
    pdf = tmp_path / "book.pdf"
    pdf.write_bytes(b"%PDF sample")
    page._apply_source_path(str(pdf))
    page._output_parent = tmp_path
    page._output_path.set_path(str(tmp_path))
    page.refresh_preset_availability()
    page._refresh_validation()
    assert page._start_button.isEnabled()


def test_new_run_page_emits_run_started(qtbot, qapp, tmp_path: Path, monkeypatch) -> None:
    controller = PipelineProcessController()
    controller.start = MagicMock()
    page = NewRunPage(LIGHT_COLORS, controller)
    qtbot.addWidget(page)
    monkeypatch.setattr(page._registry, "presets_blocked", lambda: set())
    monkeypatch.setattr(page._registry, "scan_all", lambda: [])
    pdf = tmp_path / "book.pdf"
    pdf.write_bytes(b"%PDF sample")
    page._apply_source_path(str(pdf))
    page._output_parent = tmp_path
    page._output_path.set_path(str(tmp_path))
    page._refresh_validation()

    received: list[object] = []
    page.run_started.connect(received.append)
    page._start_run()

    assert controller.start.called
    assert received