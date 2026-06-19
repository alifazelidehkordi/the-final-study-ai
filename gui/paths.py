"""Application data and managed tool directories."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QStandardPaths


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def app_data_dir() -> Path:
    root = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    path = Path(root) / "TheFinalStudyAI"
    path.mkdir(parents=True, exist_ok=True)
    return path


def tools_dir() -> Path:
    path = app_data_dir() / "tools"
    path.mkdir(parents=True, exist_ok=True)
    return path


def browser_profile_dir() -> Path:
    path = app_data_dir() / "browser_profile"
    path.mkdir(parents=True, exist_ok=True)
    return path


def profile_lock_path() -> Path:
    return browser_profile_dir() / "profile.lock"


def compatibility_manifest_path() -> Path:
    return project_root() / "schemas" / "compatibility-manifest-v1.json"


def runs_dir() -> Path:
    path = app_data_dir() / "runs"
    path.mkdir(parents=True, exist_ok=True)
    return path


@dataclass(frozen=True)
class RunArtifacts:
    base: Path
    events: Path
    manifest: Path
    log: Path
    stop_file: Path


def run_artifacts(run_id: str) -> RunArtifacts:
    base = runs_dir() / run_id
    return RunArtifacts(
        base=base,
        events=base / "events.jsonl",
        manifest=base / "run.json",
        log=base / "run.log",
        stop_file=base / "stop.requested",
    )