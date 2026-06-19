"""Platform-specific install plans and manual fallback instructions."""

from __future__ import annotations

import shutil
import sys

from gui.dependencies.manifest import CompatibilityManifest
from gui.dependencies.models import DependencyId, InstallPlan
from gui.dependencies.tool_paths import ToolPaths
from gui.paths import tools_dir


def _linux_package_manager() -> str | None:
    if shutil.which("apt"):
        return "apt"
    if shutil.which("dnf"):
        return "dnf"
    if shutil.which("pacman"):
        return "pacman"
    if shutil.which("zypper"):
        return "zypper"
    return None


def install_plan_for(
    dependency_id: DependencyId,
    *,
    manifest: CompatibilityManifest,
    tool_paths: ToolPaths,
) -> InstallPlan | None:
    builders = {
        DependencyId.PDF_CONVERSION: _pdf_conversion_plan,
        DependencyId.OCR: _ocr_plan,
        DependencyId.MINDMAP_PROJECT: lambda: _mindmap_project_plan(manifest, tool_paths),
        DependencyId.MINDMAP_PACKAGES: lambda: _mindmap_packages_plan(manifest, tool_paths),
        DependencyId.CHROME: _chrome_plan,
        DependencyId.LINUX_DESKTOP: _linux_desktop_plan,
        DependencyId.PYSIDE6: _pyside6_plan,
    }
    builder = builders.get(dependency_id)
    return builder() if builder is not None else None


def _pyside6_plan() -> InstallPlan:
    return InstallPlan(
        dependency_id=DependencyId.PYSIDE6,
        title="Install PySide6",
        summary="Install the locked GUI dependency into the active environment.",
        license_notice=None,
        requires_privilege=False,
        planned_commands=(f"{sys.executable} -m pip install 'PySide6>=6.8,<7'",),
        manual_fallback="Run the exact pip command shown above in your project virtual environment.",
    )


def _pdf_conversion_plan() -> InstallPlan:
    checkout = tools_dir() / "pdf-to-markdown"
    python_path = checkout / ".venv/bin/python"
    return InstallPlan(
        dependency_id=DependencyId.PDF_CONVERSION,
        title="Prepare PDF conversion",
        summary="Create a managed checkout and virtual environment for PyMuPDF4LLM.",
        license_notice=(
            "PyMuPDF4LLM is AGPL-3.0. Confirm you accept the license before cloning "
            "or installing the converter."
        ),
        requires_privilege=False,
        planned_commands=(
            f"git clone https://github.com/pymupdf/PyMuPDF4LLM.git {checkout}",
            f"python3 -m venv {checkout / '.venv'}",
            f"{python_path} -m pip install 'pymupdf4llm>=1.27.2.3,<2'",
        ),
        manual_fallback=(
            "Set PDF_TO_MD_PY and PDF_TO_MD_SCRIPT to an existing converter checkout "
            "with PyMuPDF4LLM installed."
        ),
    )


def _ocr_plan() -> InstallPlan:
    manager = _linux_package_manager()
    if sys.platform.startswith("linux") and manager == "apt":
        command = "sudo apt install tesseract-ocr tesseract-ocr-fas"
        manual = "Install Tesseract OCR and the Persian language pack using your distribution packages."
    elif sys.platform == "win32":
        command = "winget install --id UB-Mannheim.TesseractOCR"
        manual = "Install Tesseract OCR from the official Windows build or winget."
    else:
        command = "Install Tesseract OCR using your operating system package manager."
        manual = command
    return InstallPlan(
        dependency_id=DependencyId.OCR,
        title="Install OCR support",
        summary="Optional OCR improves scanned PDF conversion.",
        license_notice=None,
        requires_privilege=sys.platform.startswith("linux") or sys.platform == "win32",
        planned_commands=(command,),
        manual_fallback=manual,
    )


def _mindmap_project_plan(manifest: CompatibilityManifest, tool_paths: ToolPaths) -> InstallPlan:
    checkout = tools_dir() / "chatgpt-mindmap-to-xmind"
    return InstallPlan(
        dependency_id=DependencyId.MINDMAP_PROJECT,
        title="Install mind-map project",
        summary="Clone the pinned mind-map automation repository into app-managed tools.",
        license_notice=None,
        requires_privilege=False,
        planned_commands=(
            f"git clone {manifest.mindmap_repository} {checkout}",
            f"cd {checkout} && git checkout {manifest.mindmap_compatible_ref}",
            f"cd {checkout} && python3 -m venv .venv",
            f"{checkout / '.venv/bin/python'} -m pip install -r {checkout / 'requirements.txt'}",
        ),
        manual_fallback=(
            f"Clone {manifest.mindmap_repository}, check out {manifest.mindmap_compatible_ref}, "
            "run setup.sh, and set MINDMAP_PROJECT to the checkout path."
        ),
    )


def _mindmap_packages_plan(manifest: CompatibilityManifest, tool_paths: ToolPaths) -> InstallPlan:
    python_path = tool_paths.mindmap_python
    return InstallPlan(
        dependency_id=DependencyId.MINDMAP_PACKAGES,
        title="Repair mind-map packages",
        summary="Install Selenium, PyAutoGUI, and Pyperclip into the mind-map environment.",
        license_notice=None,
        requires_privilege=False,
        planned_commands=(
            (
                f"{python_path} -m pip install "
                f"'selenium{manifest.selenium}' "
                f"'pyautogui{manifest.pyautogui}' "
                f"'pyperclip{manifest.pyperclip}'"
            ),
        ),
        manual_fallback=f"Run the pip command above inside {tool_paths.mindmap_project}.",
    )


def _chrome_plan() -> InstallPlan:
    if sys.platform == "win32":
        command = "winget install --id Google.Chrome"
        manual = "Install Google Chrome or Chromium and ensure it launches normally."
    elif sys.platform == "darwin":
        command = "brew install --cask google-chrome"
        manual = "Install Google Chrome from the official installer or Homebrew if already available."
    else:
        manager = _linux_package_manager()
        if manager == "apt":
            command = "sudo apt install chromium-browser"
        elif manager == "dnf":
            command = "sudo dnf install chromium"
        else:
            command = "Install Chromium using your distribution package manager."
        manual = command
    return InstallPlan(
        dependency_id=DependencyId.CHROME,
        title="Install Chrome or Chromium",
        summary="Browser automation requires a local Chrome or Chromium executable.",
        license_notice=None,
        requires_privilege=sys.platform.startswith("linux") or sys.platform == "win32",
        planned_commands=(command,),
        manual_fallback=manual,
    )


def _linux_desktop_plan() -> InstallPlan:
    manager = _linux_package_manager()
    if manager == "apt":
        command = "sudo apt install python3-tk scrot"
    elif manager == "dnf":
        command = "sudo dnf install python3-tkinter scrot"
    else:
        command = "Install Tk and screenshot/input packages using your distribution tools."
    return InstallPlan(
        dependency_id=DependencyId.LINUX_DESKTOP,
        title="Install Linux desktop support",
        summary="PyAutoGUI needs Tk, a display server, and screenshot utilities on Linux.",
        license_notice=None,
        requires_privilege=True,
        planned_commands=(command,),
        manual_fallback=command,
    )