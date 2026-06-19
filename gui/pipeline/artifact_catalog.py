"""Summarize validated and discovered run artifacts for Results."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gui.paths import project_root

_ROOT = project_root()
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.artifact_validators import (  # noqa: E402
    ArtifactValidationError,
    sha256_file,
    validate_index_markdown,
    validate_markdown,
    validate_parts_manifest,
)


@dataclass(frozen=True)
class ArtifactEntry:
    group: str
    label: str
    path: Path
    valid: bool
    changed: bool
    detail: str | None = None


def _manifest_hash(path: Path, manifest: dict[str, Any]) -> str | None:
    for artifact in manifest.get("artifacts", []):
        if not isinstance(artifact, dict):
            continue
        if artifact.get("path") == str(path):
            recorded = artifact.get("sha256")
            if isinstance(recorded, str):
                return recorded
    return None


def _changed_warning(path: Path, manifest: dict[str, Any]) -> bool:
    if not path.is_file():
        return False
    recorded = _manifest_hash(path, manifest)
    if recorded is None:
        return False
    try:
        return sha256_file(path) != recorded
    except OSError:
        return True


def catalog_run_artifacts(work_dir: Path, manifest: dict[str, Any]) -> list[ArtifactEntry]:
    entries: list[ArtifactEntry] = []
    parts_manifest = work_dir / "parts-manifest.json"
    part_count = 0
    if parts_manifest.is_file():
        try:
            parts_data = validate_parts_manifest(parts_manifest)
            parts = parts_data.get("parts", [])
            part_count = len(parts) if isinstance(parts, list) else 0
        except ArtifactValidationError as exc:
            entries.append(
                ArtifactEntry(
                    group="parts",
                    label="Study parts",
                    path=parts_manifest,
                    valid=False,
                    changed=False,
                    detail=str(exc),
                )
            )

    markdown_path: Path | None = None
    source = manifest.get("source")
    if isinstance(source, dict) and source.get("kind") == "pdf":
        pdf_path = source.get("path")
        if isinstance(pdf_path, str):
            candidate = Path(pdf_path).with_suffix(".md")
            if candidate.is_file():
                markdown_path = candidate
    if markdown_path is None:
        markdown_candidates = [
            candidate
            for candidate in work_dir.glob("*.md")
            if candidate.name not in {"STUDY_INDEX.md", "SEGMENTATION_PREVIEW.md"}
        ]
        if markdown_candidates:
            markdown_path = markdown_candidates[0]
    if markdown_path is not None:
        try:
            validate_markdown(markdown_path)
            entries.append(
                ArtifactEntry(
                    group="markdown",
                    label="Source Markdown",
                    path=markdown_path,
                    valid=True,
                    changed=_changed_warning(markdown_path, manifest),
                )
            )
        except ArtifactValidationError as exc:
            entries.append(
                ArtifactEntry(
                    group="markdown",
                    label="Source Markdown",
                    path=markdown_path,
                    valid=False,
                    changed=False,
                    detail=str(exc),
                )
            )

    index_md = work_dir / "STUDY_INDEX.md"
    if index_md.is_file():
        try:
            validate_index_markdown(index_md, expected_parts=part_count or 1)
            entries.append(
                ArtifactEntry(
                    group="index",
                    label="Study Index (Markdown)",
                    path=index_md,
                    valid=True,
                    changed=_changed_warning(index_md, manifest),
                )
            )
        except ArtifactValidationError as exc:
            entries.append(
                ArtifactEntry(
                    group="index",
                    label="Study Index (Markdown)",
                    path=index_md,
                    valid=False,
                    changed=False,
                    detail=str(exc),
                )
            )

    index_pdf = work_dir / "STUDY_INDEX.pdf"
    if index_pdf.is_file():
        entries.append(
            ArtifactEntry(
                group="index",
                label="Study Index (PDF)",
                path=index_pdf,
                valid=True,
                changed=_changed_warning(index_pdf, manifest),
            )
        )

    parts_dir = work_dir / "parts"
    if parts_dir.is_dir():
        entries.append(
            ArtifactEntry(
                group="parts",
                label="Segmented parts folder",
                path=parts_dir,
                valid=part_count > 0,
                changed=False,
                detail=f"{part_count} parts" if part_count else None,
            )
        )

    for folder, group, label in (
        (work_dir / "opml", "opml", "OPML outputs"),
        (work_dir / "xmind", "xmind", "XMind outputs"),
    ):
        if folder.is_dir() and any(folder.iterdir()):
            entries.append(
                ArtifactEntry(
                    group=group,
                    label=label,
                    path=folder,
                    valid=True,
                    changed=False,
                    detail=f"{len(list(folder.glob('*')))} files",
                )
            )

    preview = work_dir / "SEGMENTATION_PREVIEW.md"
    if preview.is_file():
        entries.append(
            ArtifactEntry(
                group="review",
                label="Segmentation preview",
                path=preview,
                valid=True,
                changed=False,
            )
        )
    return entries