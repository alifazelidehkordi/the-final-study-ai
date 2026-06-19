"""Resolved external tool locations used by probes and the pipeline."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ToolPaths:
    pdf_python: Path
    pdf_script: Path
    mindmap_project: Path
    mindmap_python: Path
    mindmap_pipeline: Path
    prompt_file: Path
    chrome_binary: Path | None
    browser_profile_dir: Path


def discover_mindmap_python(project: Path) -> Path:
    candidates = (
        project / ".venv/Scripts/python.exe",
        project / ".venv/bin/python",
        project / ".venv-linux/bin/python",
    )
    return next((candidate for candidate in candidates if candidate.is_file()), candidates[1])


def default_tool_paths(*, browser_profile_dir: Path) -> ToolPaths:
    home = Path.home()
    mindmap_project = Path(
        os.environ.get("MINDMAP_PROJECT", str(home / "projects/chatgpt-mindmap-to-xmind"))
    ).expanduser()
    return ToolPaths(
        pdf_python=Path(
            os.environ.get(
                "PDF_TO_MD_PY",
                str(home / ".grok/skills/pdf-to-markdown/.venv/bin/python"),
            )
        ).expanduser(),
        pdf_script=Path(
            os.environ.get(
                "PDF_TO_MD_SCRIPT",
                str(home / ".grok/skills/pdf-to-markdown/scripts/convert_pdf.py"),
            )
        ).expanduser(),
        mindmap_project=mindmap_project,
        mindmap_python=discover_mindmap_python(mindmap_project),
        mindmap_pipeline=mindmap_project / "scripts/pipeline.py",
        prompt_file=Path(
            os.environ.get(
                "PROMPT_FILE",
                str(mindmap_project / "prompts/prompt-mind-map.md"),
            )
        ).expanduser(),
        chrome_binary=_find_chrome_binary(),
        browser_profile_dir=browser_profile_dir,
    )


def _find_chrome_binary() -> Path | None:
    import shutil

    candidates = (
        Path("/usr/bin/google-chrome"),
        Path("/usr/bin/google-chrome-stable"),
        Path("/usr/bin/chromium"),
        Path("/usr/bin/chromium-browser"),
        Path("/snap/bin/chromium"),
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        found = shutil.which(name)
        if found:
            return Path(found)
    return None