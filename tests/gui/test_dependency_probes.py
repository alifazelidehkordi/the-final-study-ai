from __future__ import annotations

import sys
from pathlib import Path

import pytest

from gui.dependencies.manifest import load_compatibility_manifest
from gui.dependencies.models import DependencyHealth, DependencyId
from gui.dependencies.probes import (
    probe_linux_desktop,
    probe_mindmap_project,
    probe_profile_login,
    probe_python,
)
from gui.dependencies.registry import DependencyRegistry
from gui.dependencies.tool_paths import ToolPaths
from gui.settings import AppSettings


def test_probe_python_reports_runtime_health() -> None:
    manifest = load_compatibility_manifest()
    report = probe_python(manifest)
    assert report.dependency_id == DependencyId.PYTHON
    supported = sys.version_info >= (3, 10) and sys.version_info < (3, 14)
    expected = DependencyHealth.READY if supported else DependencyHealth.UNSUPPORTED
    assert report.health == expected
    assert report.detected_version == ".".join(map(str, sys.version_info[:3]))


def test_registry_attaches_install_plan_for_missing_pdf_converter(tmp_path: Path) -> None:
    tool_paths = ToolPaths(
        pdf_python=tmp_path / "missing-python",
        pdf_script=tmp_path / "missing-script.py",
        mindmap_project=tmp_path / "mindmap",
        mindmap_python=tmp_path / "mindmap/.venv/bin/python",
        mindmap_pipeline=tmp_path / "mindmap/scripts/pipeline.py",
        prompt_file=tmp_path / "mindmap/prompts/prompt-mind-map.md",
        chrome_binary=None,
        browser_profile_dir=tmp_path / "profile",
    )
    registry = DependencyRegistry(
        settings=AppSettings(),
        tool_paths=tool_paths,
    )
    report = registry.report_for(DependencyId.PDF_CONVERSION)
    assert report.health == DependencyHealth.MISSING
    assert report.install_plan is not None
    assert "AGPL" in (report.install_plan.license_notice or "")


def test_probe_linux_desktop_rejects_wayland(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("gui.dependencies.probes.sys.platform", "linux")
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    report = probe_linux_desktop()
    assert report.health == DependencyHealth.UNSUPPORTED
    assert "Wayland" in (report.detail or "")
    assert "complete" in report.blocks_presets


def test_probe_mindmap_project_blocks_macos(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("gui.dependencies.probes.sys.platform", "darwin")
    manifest = load_compatibility_manifest()
    tool_paths = ToolPaths(
        pdf_python=tmp_path / "python",
        pdf_script=tmp_path / "convert.py",
        mindmap_project=tmp_path / "mindmap",
        mindmap_python=tmp_path / "mindmap/.venv/bin/python",
        mindmap_pipeline=tmp_path / "mindmap/scripts/pipeline.py",
        prompt_file=tmp_path / "mindmap/prompt.md",
        chrome_binary=None,
        browser_profile_dir=tmp_path / "profile",
    )
    (tool_paths.mindmap_project / "scripts").mkdir(parents=True)
    tool_paths.mindmap_pipeline.write_text("print('ok')\n", encoding="utf-8")
    report = probe_mindmap_project(tool_paths, manifest)
    assert report.health == DependencyHealth.UNSUPPORTED
    assert "macOS" in (report.detail or "")
    assert report.blocks_presets == ("complete", "mindmaps_only")


def test_profile_login_unknown_without_probe_history(tmp_path: Path) -> None:
    tool_paths = ToolPaths(
        pdf_python=tmp_path / "python",
        pdf_script=tmp_path / "convert.py",
        mindmap_project=tmp_path / "mindmap",
        mindmap_python=tmp_path / "mindmap/.venv/bin/python",
        mindmap_pipeline=tmp_path / "mindmap/scripts/pipeline.py",
        prompt_file=tmp_path / "mindmap/prompt.md",
        chrome_binary=None,
        browser_profile_dir=tmp_path / "profile",
    )
    report = probe_profile_login(tool_paths, AppSettings(last_login_probe_status="unknown"))
    assert report.dependency_id == DependencyId.PROFILE_LOGIN
    assert report.health == DependencyHealth.UNKNOWN