"""Open files and folders with the native desktop handler."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices


def open_path(path: Path) -> bool:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        return False
    return QDesktopServices.openUrl(QUrl.fromLocalFile(str(resolved)))


def open_folder(path: Path) -> bool:
    resolved = path.expanduser().resolve()
    target = resolved if resolved.is_dir() else resolved.parent
    return open_path(target)