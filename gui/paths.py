"""Application data and managed tool directories."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QStandardPaths


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
    return Path(__file__).resolve().parents[1] / "schemas" / "compatibility-manifest-v1.json"