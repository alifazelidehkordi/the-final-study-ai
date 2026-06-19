"""Discover and summarize persisted pipeline runs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gui.paths import run_artifacts, runs_dir
from gui.pipeline.contracts_bridge import ContractError, load_run_manifest


@dataclass(frozen=True)
class RunSummary:
    run_id: str
    manifest_path: Path
    status: str
    preset: str
    updated_at: str
    work_dir: Path
    source_label: str
    manifest: dict[str, Any]


def _source_label(manifest: dict[str, Any]) -> str:
    source = manifest.get("source", {})
    if not isinstance(source, dict):
        return "Unknown source"
    path = source.get("path")
    if isinstance(path, str):
        return path
    return "Unknown source"


def load_run_summary(manifest_path: Path) -> RunSummary:
    manifest = load_run_manifest(manifest_path)
    paths = manifest.get("paths", {})
    work_dir = Path(paths.get("work_dir", manifest_path.parent))
    return RunSummary(
        run_id=str(manifest["run_id"]),
        manifest_path=manifest_path,
        status=str(manifest["status"]),
        preset=str(manifest["preset"]),
        updated_at=str(manifest["updated_at"]),
        work_dir=work_dir,
        source_label=_source_label(manifest),
        manifest=manifest,
    )


def list_runs() -> list[RunSummary]:
    summaries: list[RunSummary] = []
    for manifest_path in runs_dir().glob("*/run.json"):
        try:
            summaries.append(load_run_summary(manifest_path))
        except (ContractError, KeyError, TypeError):
            continue
    return sorted(summaries, key=lambda item: item.updated_at, reverse=True)


def summary_for_run_id(run_id: str) -> RunSummary | None:
    manifest_path = run_artifacts(run_id).manifest
    if not manifest_path.is_file():
        return None
    try:
        return load_run_summary(manifest_path)
    except (ContractError, KeyError, TypeError):
        return None