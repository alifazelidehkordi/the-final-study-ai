"""Load the pinned compatibility manifest."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gui.paths import compatibility_manifest_path


@dataclass(frozen=True)
class CompatibilityManifest:
    python: str
    pyside6: str
    pymupdf4llm: str
    selenium: str
    pyautogui: str
    pyperclip: str
    mindmap_repository: str
    mindmap_compatible_ref: str


def load_compatibility_manifest(path: Path | None = None) -> CompatibilityManifest:
    manifest_path = path or compatibility_manifest_path()
    payload: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    if payload.get("schema") != "final-study.compatibility" or payload.get("version") != 1:
        raise ValueError("Unsupported compatibility manifest schema.")
    return CompatibilityManifest(
        python=str(payload["python"]),
        pyside6=str(payload["pyside6"]),
        pymupdf4llm=str(payload["pymupdf4llm"]),
        selenium=str(payload["selenium"]),
        pyautogui=str(payload["pyautogui"]),
        pyperclip=str(payload["pyperclip"]),
        mindmap_repository=str(payload["mindmap_repository"]),
        mindmap_compatible_ref=str(payload["mindmap_compatible_ref"]),
    )