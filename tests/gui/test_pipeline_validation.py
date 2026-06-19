from __future__ import annotations

from pathlib import Path

import pytest

from gui.pipeline.models import RunPreset, RunRequest
from gui.pipeline.validation import (
    ValidationSeverity,
    check_disk_space,
    disk_space_thresholds,
    validate_run_request,
)


def test_validate_pdf_requires_existing_file(tmp_path: Path) -> None:
    request = RunRequest(preset=RunPreset.COMPLETE, pdf_path=tmp_path / "missing.pdf")
    issues = validate_run_request(request)
    assert any(issue.code == "E_INPUT_NOT_FOUND" for issue in issues)


def test_validate_work_dir_requires_parts_manifest(tmp_path: Path) -> None:
    work = tmp_path / "work"
    work.mkdir()
    request = RunRequest(preset=RunPreset.MINDMAPS_ONLY, work_dir=work)
    issues = validate_run_request(request)
    codes = {issue.code for issue in issues}
    assert "E_INPUT_INVALID" in codes


def test_disk_space_thresholds_follow_contract() -> None:
    required, warning = disk_space_thresholds(100)
    assert required == 1024**3
    assert warning == 5 * 1024**3
    required_large, warning_large = disk_space_thresholds(2 * 1024**3)
    assert required_large == 6 * 1024**3
    assert warning_large == 10 * 1024**3


def test_validate_run_request_reports_disk_warning(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pdf = tmp_path / "book.pdf"
    pdf.write_bytes(b"x" * 1024)
    request = RunRequest(preset=RunPreset.COMPLETE, pdf_path=pdf, output_parent=tmp_path)

    class _Usage:
        free = 2 * 1024**3

    monkeypatch.setattr("gui.pipeline.validation.shutil.disk_usage", lambda _path: _Usage())
    issues = validate_run_request(request)
    warnings = [issue for issue in issues if issue.severity == ValidationSeverity.WARNING]
    assert warnings
    assert warnings[0].code == "E_DISK_SPACE"


def test_check_disk_space_hard_fail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class _Usage:
        free = 512 * 1024**2

    monkeypatch.setattr("gui.pipeline.validation.shutil.disk_usage", lambda _path: _Usage())
    result = check_disk_space(1024, tmp_path)
    assert result.hard_fail