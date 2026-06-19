"""Validate New Run inputs and disk-space thresholds."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from gui.pipeline.models import RunPreset, RunRequest

GIB = 1024**3


class ValidationSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR


@dataclass(frozen=True)
class DiskSpaceCheck:
    source_bytes: int
    free_bytes: int
    required_bytes: int
    warning_bytes: int

    @property
    def hard_fail(self) -> bool:
        return self.free_bytes < self.required_bytes

    @property
    def needs_warning(self) -> bool:
        return not self.hard_fail and self.free_bytes < self.warning_bytes


def directory_size(path: Path) -> int:
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            total += item.stat().st_size
    return total


def disk_space_thresholds(source_bytes: int) -> tuple[int, int]:
    required = max(GIB, source_bytes * 3)
    warning = max(5 * GIB, source_bytes * 5)
    return required, warning


def check_disk_space(source_bytes: int, target_dir: Path) -> DiskSpaceCheck:
    target_dir.mkdir(parents=True, exist_ok=True)
    usage = shutil.disk_usage(target_dir)
    required, warning = disk_space_thresholds(source_bytes)
    return DiskSpaceCheck(
        source_bytes=source_bytes,
        free_bytes=usage.free,
        required_bytes=required,
        warning_bytes=warning,
    )


def validate_pdf(path: Path | None) -> list[ValidationIssue]:
    if path is None:
        return [
            ValidationIssue(
                code="E_INPUT_NOT_FOUND",
                message="Select a PDF file to continue.",
            )
        ]
    resolved = path.expanduser()
    if not resolved.is_file():
        return [
            ValidationIssue(
                code="E_INPUT_NOT_FOUND",
                message=f"PDF not found: {resolved}",
            )
        ]
    if resolved.suffix.lower() != ".pdf":
        return [
            ValidationIssue(
                code="E_INPUT_INVALID",
                message="The selected file is not a PDF.",
            )
        ]
    if resolved.stat().st_size == 0:
        return [
            ValidationIssue(
                code="E_INPUT_INVALID",
                message="The selected PDF is empty.",
            )
        ]
    return []


def validate_work_dir(path: Path | None) -> list[ValidationIssue]:
    if path is None:
        return [
            ValidationIssue(
                code="E_INPUT_NOT_FOUND",
                message="Select an existing work directory to continue.",
            )
        ]
    resolved = path.expanduser()
    if not resolved.is_dir():
        return [
            ValidationIssue(
                code="E_INPUT_NOT_FOUND",
                message=f"Work directory not found: {resolved}",
            )
        ]
    parts = resolved / "parts"
    manifest = resolved / "parts-manifest.json"
    issues: list[ValidationIssue] = []
    if not parts.is_dir():
        issues.append(
            ValidationIssue(
                code="E_INPUT_INVALID",
                message="The work directory must contain a parts/ folder.",
            )
        )
    if not manifest.is_file():
        issues.append(
            ValidationIssue(
                code="E_INPUT_INVALID",
                message="The work directory must contain parts-manifest.json.",
            )
        )
    return issues


def resolve_work_dir(request: RunRequest) -> Path:
    if request.preset == RunPreset.MINDMAPS_ONLY:
        if request.work_dir is None:
            raise ValueError("Mind Maps Only requires a work directory.")
        return request.work_dir.expanduser().resolve()
    if request.pdf_path is None:
        raise ValueError("PDF presets require a PDF path.")
    if request.advanced.custom_work_dir is not None:
        return request.advanced.custom_work_dir.expanduser().resolve()
    pdf = request.pdf_path.expanduser().resolve()
    if request.output_parent is not None:
        return (request.output_parent.expanduser().resolve() / f"{pdf.stem}_work").resolve()
    return pdf.with_name(f"{pdf.stem}_work").resolve()


def source_bytes_for_request(request: RunRequest) -> int:
    if request.preset == RunPreset.MINDMAPS_ONLY:
        if request.work_dir is None:
            return 0
        return directory_size(request.work_dir.expanduser().resolve())
    if request.pdf_path is None:
        return 0
    return request.pdf_path.expanduser().resolve().stat().st_size


def validate_run_request(request: RunRequest) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if request.preset == RunPreset.MINDMAPS_ONLY:
        issues.extend(validate_work_dir(request.work_dir))
    else:
        issues.extend(validate_pdf(request.pdf_path))
        if not issues:
            try:
                work_dir = resolve_work_dir(request)
            except ValueError as exc:
                issues.append(
                    ValidationIssue(
                        code="E_INPUT_INVALID",
                        message=str(exc),
                    )
                )
            else:
                parent = work_dir.parent
                if not parent.exists():
                    issues.append(
                        ValidationIssue(
                            code="E_INPUT_NOT_FOUND",
                            message=f"Output parent directory not found: {parent}",
                        )
                    )
                else:
                    disk = check_disk_space(source_bytes_for_request(request), parent)
                    if disk.hard_fail:
                        issues.append(
                            ValidationIssue(
                                code="E_DISK_SPACE",
                                message=(
                                    "Not enough free space. "
                                    f"Need at least {disk.required_bytes // GIB} GiB free."
                                ),
                            )
                        )
                    elif disk.needs_warning:
                        issues.append(
                            ValidationIssue(
                                code="E_DISK_SPACE",
                                message=(
                                    "Free space is below the recommended threshold. "
                                    f"Only {disk.free_bytes // GIB} GiB is available."
                                ),
                                severity=ValidationSeverity.WARNING,
                            )
                        )
    if request.preset == RunPreset.MINDMAPS_ONLY and not issues:
        work_dir = resolve_work_dir(request)
        disk = check_disk_space(source_bytes_for_request(request), work_dir)
        if disk.hard_fail:
            issues.append(
                ValidationIssue(
                    code="E_DISK_SPACE",
                    message=(
                        "Not enough free space. "
                        f"Need at least {disk.required_bytes // GIB} GiB free."
                    ),
                )
            )
        elif disk.needs_warning:
            issues.append(
                ValidationIssue(
                    code="E_DISK_SPACE",
                    message=(
                        "Free space is below the recommended threshold. "
                        f"Only {disk.free_bytes // GIB} GiB is available."
                    ),
                    severity=ValidationSeverity.WARNING,
                )
            )
    if request.advanced.limit is not None and request.advanced.limit < 1:
        issues.append(
            ValidationIssue(
                code="E_INPUT_INVALID",
                message="Item limit must be a positive integer.",
            )
        )
    return issues