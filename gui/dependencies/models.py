"""Dependency health and install-plan models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class DependencyId(str, Enum):
    PYTHON = "python"
    PYSIDE6 = "pyside6"
    PDF_CONVERSION = "pdf_conversion"
    OCR = "ocr"
    MINDMAP_PROJECT = "mindmap_project"
    MINDMAP_PACKAGES = "mindmap_packages"
    CHROME = "chrome"
    LINUX_DESKTOP = "linux_desktop"
    PROFILE_LOGIN = "profile_login"


class DependencyHealth(str, Enum):
    READY = "ready"
    MISSING = "missing"
    UNSUPPORTED = "unsupported"
    REPAIRABLE = "repairable"
    CHECKING = "checking"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class InstallPlan:
    dependency_id: DependencyId
    title: str
    summary: str
    license_notice: str | None
    requires_privilege: bool
    planned_commands: tuple[str, ...]
    manual_fallback: str


@dataclass(frozen=True)
class DependencyReport:
    dependency_id: DependencyId
    title: str
    purpose: str
    health: DependencyHealth
    detected_version: str | None = None
    detected_path: str | None = None
    detail: str | None = None
    install_plan: InstallPlan | None = None
    blocks_presets: tuple[str, ...] = field(default_factory=tuple)