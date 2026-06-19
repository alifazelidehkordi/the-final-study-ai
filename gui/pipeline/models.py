"""Run configuration models for pipeline orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class RunPreset(str, Enum):
    COMPLETE = "complete"
    MARKDOWN_INDEX = "markdown_index"
    MINDMAPS_ONLY = "mindmaps_only"


@dataclass(frozen=True)
class AdvancedOptions:
    granularity: str = "normal"
    ocr: str = "off"
    index_language: str = "Persian"
    limit: int | None = None
    overwrite: bool = False
    custom_work_dir: Path | None = None


@dataclass(frozen=True)
class RunRequest:
    preset: RunPreset
    pdf_path: Path | None = None
    work_dir: Path | None = None
    output_parent: Path | None = None
    advanced: AdvancedOptions = AdvancedOptions()