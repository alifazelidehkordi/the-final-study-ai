"""Read-only dependency health probes."""

from __future__ import annotations

import importlib.util
import os
import platform
import shutil
import subprocess
import sys
from importlib import metadata
from pathlib import Path

from gui.dependencies.manifest import CompatibilityManifest
from gui.dependencies.models import DependencyHealth, DependencyId, DependencyReport
from gui.dependencies.profile_lock import read_lock_status
from gui.dependencies.tool_paths import ToolPaths
from gui.paths import profile_lock_path
from gui.settings import AppSettings


def _version_in_range(version: str, specifier: str) -> bool:
    from packaging.specifiers import SpecifierSet
    from packaging.version import Version

    return Version(version) in SpecifierSet(specifier)


def probe_python(manifest: CompatibilityManifest) -> DependencyReport:
    version = platform.python_version()
    supported = _version_in_range(version, manifest.python)
    health = DependencyHealth.READY if supported else DependencyHealth.UNSUPPORTED
    return DependencyReport(
        dependency_id=DependencyId.PYTHON,
        title="Python",
        purpose="Runs the orchestrator, GUI, and child tool environments.",
        health=health,
        detected_version=version,
        detected_path=sys.executable,
        detail=None if supported else f"Requires {manifest.python}.",
        blocks_presets=() if supported else ("complete", "markdown_index", "mindmaps_only"),
    )


def probe_pyside6(manifest: CompatibilityManifest) -> DependencyReport:
    spec = importlib.util.find_spec("PySide6")
    if spec is None:
        return DependencyReport(
            dependency_id=DependencyId.PYSIDE6,
            title="PySide6",
            purpose="Desktop GUI toolkit.",
            health=DependencyHealth.MISSING,
            detail="PySide6 is not installed in the active environment.",
            blocks_presets=("complete", "markdown_index", "mindmaps_only"),
        )
    version = metadata.version("PySide6")
    supported = _version_in_range(version, manifest.pyside6)
    health = DependencyHealth.READY if supported else DependencyHealth.REPAIRABLE
    return DependencyReport(
        dependency_id=DependencyId.PYSIDE6,
        title="PySide6",
        purpose="Desktop GUI toolkit.",
        health=health,
        detected_version=version,
        detail=None if supported else f"Requires {manifest.pyside6}.",
        blocks_presets=() if supported else ("complete", "markdown_index", "mindmaps_only"),
    )


def probe_pdf_conversion(
    tool_paths: ToolPaths,
    manifest: CompatibilityManifest,
) -> DependencyReport:
    python_path = tool_paths.pdf_python
    script_path = tool_paths.pdf_script
    if not python_path.is_file() or not script_path.is_file():
        return DependencyReport(
            dependency_id=DependencyId.PDF_CONVERSION,
            title="PDF conversion",
            purpose="Converts source PDFs into Markdown for segmentation.",
            health=DependencyHealth.MISSING,
            detected_path=str(script_path),
            detail="PDF converter Python or script path is missing.",
            blocks_presets=("complete", "markdown_index"),
        )
    result = subprocess.run(
        [str(python_path), "-c", "import pymupdf4llm; print(pymupdf4llm.__version__)"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return DependencyReport(
            dependency_id=DependencyId.PDF_CONVERSION,
            title="PDF conversion",
            purpose="Converts source PDFs into Markdown for segmentation.",
            health=DependencyHealth.REPAIRABLE,
            detected_path=str(script_path),
            detail=result.stderr.strip() or "PyMuPDF4LLM is not importable.",
            blocks_presets=("complete", "markdown_index"),
        )
    version = result.stdout.strip()
    supported = _version_in_range(version, manifest.pymupdf4llm)
    health = DependencyHealth.READY if supported else DependencyHealth.REPAIRABLE
    return DependencyReport(
        dependency_id=DependencyId.PDF_CONVERSION,
        title="PDF conversion",
        purpose="Converts source PDFs into Markdown for segmentation.",
        health=health,
        detected_version=version,
        detected_path=str(script_path),
        detail=None if supported else f"Requires {manifest.pymupdf4llm}.",
        blocks_presets=() if supported else ("complete", "markdown_index"),
    )


def probe_ocr() -> DependencyReport:
    tesseract = shutil.which("tesseract")
    health = DependencyHealth.READY if tesseract else DependencyHealth.MISSING
    return DependencyReport(
        dependency_id=DependencyId.OCR,
        title="OCR",
        purpose="Optional OCR for scanned PDFs when auto mode is enabled.",
        health=health,
        detected_path=tesseract,
        detail=None if tesseract else "Tesseract was not found on PATH.",
        blocks_presets=(),
    )


def probe_mindmap_project(
    tool_paths: ToolPaths,
    manifest: CompatibilityManifest,
) -> DependencyReport:
    project = tool_paths.mindmap_project
    pipeline = tool_paths.mindmap_pipeline
    if not project.is_dir() or not pipeline.is_file():
        return DependencyReport(
            dependency_id=DependencyId.MINDMAP_PROJECT,
            title="Mind-map project",
            purpose="Provides OPML and XMind browser automation.",
            health=DependencyHealth.MISSING,
            detected_path=str(project),
            detail="Mind-map checkout or scripts/pipeline.py is missing.",
            blocks_presets=("complete", "mindmaps_only"),
        )
    ref = _git_head_ref(project)
    expected = manifest.mindmap_compatible_ref
    compatible = ref == expected or ref.endswith(expected)
    health = DependencyHealth.READY if compatible else DependencyHealth.REPAIRABLE
    return DependencyReport(
        dependency_id=DependencyId.MINDMAP_PROJECT,
        title="Mind-map project",
        purpose="Provides OPML and XMind browser automation.",
        health=health,
        detected_path=str(project),
        detected_version=ref,
        detail=None if compatible else f"Expected ref {manifest.mindmap_compatible_ref}.",
        blocks_presets=() if compatible else ("complete", "mindmaps_only"),
    )


def probe_mindmap_packages(
    tool_paths: ToolPaths,
    manifest: CompatibilityManifest,
) -> DependencyReport:
    python_path = tool_paths.mindmap_python
    if not python_path.is_file():
        return DependencyReport(
            dependency_id=DependencyId.MINDMAP_PACKAGES,
            title="Mind-map packages",
            purpose="Selenium and desktop automation libraries for mind-map runs.",
            health=DependencyHealth.MISSING,
            detected_path=str(python_path),
            detail="Mind-map Python environment was not found.",
            blocks_presets=("complete", "mindmaps_only"),
        )
    result = subprocess.run(
        [
            str(python_path),
            "-c",
            "import selenium, pyautogui, pyperclip; "
            "print(selenium.__version__)",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return DependencyReport(
            dependency_id=DependencyId.MINDMAP_PACKAGES,
            title="Mind-map packages",
            purpose="Selenium and desktop automation libraries for mind-map runs.",
            health=DependencyHealth.REPAIRABLE,
            detected_path=str(python_path),
            detail=result.stderr.strip() or "Required imports failed.",
            blocks_presets=("complete", "mindmaps_only"),
        )
    version = result.stdout.strip()
    supported = _version_in_range(version, manifest.selenium)
    health = DependencyHealth.READY if supported else DependencyHealth.REPAIRABLE
    return DependencyReport(
        dependency_id=DependencyId.MINDMAP_PACKAGES,
        title="Mind-map packages",
        purpose="Selenium and desktop automation libraries for mind-map runs.",
        health=health,
        detected_version=version,
        detected_path=str(python_path),
        detail=None if supported else f"Requires selenium{manifest.selenium}.",
        blocks_presets=() if supported else ("complete", "mindmaps_only"),
    )


def probe_chrome(tool_paths: ToolPaths) -> DependencyReport:
    binary = tool_paths.chrome_binary
    if binary is None or not binary.is_file():
        return DependencyReport(
            dependency_id=DependencyId.CHROME,
            title="Chrome / Chromium",
            purpose="Browser automation launches a local Chrome or Chromium binary.",
            health=DependencyHealth.MISSING,
            detail="No Chrome or Chromium executable was detected.",
            blocks_presets=("complete", "mindmaps_only"),
        )
    return DependencyReport(
        dependency_id=DependencyId.CHROME,
        title="Chrome / Chromium",
        purpose="Browser automation launches a local Chrome or Chromium binary.",
        health=DependencyHealth.READY,
        detected_path=str(binary),
        blocks_presets=(),
    )


def probe_linux_desktop() -> DependencyReport:
    if not sys.platform.startswith("linux"):
        return DependencyReport(
            dependency_id=DependencyId.LINUX_DESKTOP,
            title="Linux desktop support",
            purpose="Screenshot and input automation on Linux desktops.",
            health=DependencyHealth.READY,
            detail="Not required on this platform.",
            blocks_presets=(),
        )
    display = os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
    tk_ready = importlib.util.find_spec("tkinter") is not None
    scrot = shutil.which("scrot") is not None
    if display and tk_ready and scrot:
        health = DependencyHealth.READY
        detail = None
    elif display and tk_ready:
        health = DependencyHealth.REPAIRABLE
        detail = "Screenshot utility scrot was not found."
    else:
        health = DependencyHealth.MISSING
        detail = "DISPLAY/WAYLAND_DISPLAY or Tkinter is unavailable."
    return DependencyReport(
        dependency_id=DependencyId.LINUX_DESKTOP,
        title="Linux desktop support",
        purpose="Screenshot and input automation on Linux desktops.",
        health=health,
        detail=detail,
        blocks_presets=("complete", "mindmaps_only") if health != DependencyHealth.READY else (),
    )


def probe_profile_login(tool_paths: ToolPaths, settings: AppSettings) -> DependencyReport:
    lock = read_lock_status(profile_lock_path())
    if lock.locked:
        return DependencyReport(
            dependency_id=DependencyId.PROFILE_LOGIN,
            title="ChatGPT profile",
            purpose="Visible login probe uses the app-managed browser profile.",
            health=DependencyHealth.CHECKING,
            detail=f"Profile locked by {lock.owner or 'another session'}.",
            blocks_presets=("complete", "mindmaps_only"),
        )
    status = settings.last_login_probe_status
    if status == "ready":
        health = DependencyHealth.READY
        detail = "Last visible login probe found a usable editor."
    elif status == "needs_login":
        health = DependencyHealth.MISSING
        detail = "Last probe did not find a usable ChatGPT editor."
    else:
        health = DependencyHealth.UNKNOWN
        detail = "Run the visible login probe from Setup."
    return DependencyReport(
        dependency_id=DependencyId.PROFILE_LOGIN,
        title="ChatGPT profile",
        purpose="Visible login probe uses the app-managed browser profile.",
        health=health,
        detail=detail,
        blocks_presets=() if health == DependencyHealth.READY else ("complete", "mindmaps_only"),
    )


def _git_head_ref(project: Path) -> str:
    head = project / ".git/HEAD"
    if not head.is_file():
        return "unknown"
    content = head.read_text(encoding="utf-8").strip()
    if content.startswith("ref:"):
        ref = content.split("/", maxsplit=2)[-1]
        return ref
    return content[:12]