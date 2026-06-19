from __future__ import annotations

import sys
from pathlib import Path

from gui.dependencies.manifest import load_compatibility_manifest
from gui.dependencies.models import DependencyHealth, DependencyId
from gui.dependencies.probes import probe_profile_login, probe_python
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