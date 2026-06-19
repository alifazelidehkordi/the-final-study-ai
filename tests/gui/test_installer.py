from __future__ import annotations

from gui.dependencies.installer import is_runnable_install_command


def test_installer_allows_python_pip_commands() -> None:
    assert is_runnable_install_command("python3 -m pip install 'PySide6>=6.8,<7'")
    assert is_runnable_install_command("/usr/bin/python3.12 -m pip install selenium")


def test_installer_rejects_privileged_or_compound_commands() -> None:
    assert not is_runnable_install_command("sudo apt install chromium-browser")
    assert not is_runnable_install_command("cd /tmp && python3 -m pip install selenium")
    assert not is_runnable_install_command("winget install --id Google.Chrome")