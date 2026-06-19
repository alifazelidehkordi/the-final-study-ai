"""Run user-confirmed, non-privileged install commands."""

from __future__ import annotations

import shlex
from pathlib import Path

from PySide6.QtCore import QObject, QProcess


def is_runnable_install_command(command: str) -> bool:
    argv = shlex.split(command.strip())
    if not argv:
        return False
    if argv[0] == "sudo" or "&&" in command:
        return False
    program_name = Path(argv[0]).name
    if program_name in {"python", "python3", "pip", "pip3"}:
        return True
    if program_name == "git" and len(argv) >= 2 and argv[1] == "clone":
        return True
    return program_name.startswith("python")


def run_confirmed_install_command(command: str, parent: QObject | None = None) -> int:
    stripped = command.strip()
    if not is_runnable_install_command(stripped):
        return 1
    argv = shlex.split(stripped)
    process = QProcess(parent)
    process.start(argv[0], argv[1:])
    if not process.waitForFinished(-1):
        return 1
    return process.exitCode()