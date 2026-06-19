from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_validate_gui_resources_passes() -> None:
    script = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "validate_gui_resources.py"
    completed = subprocess.run(
        [sys.executable, str(script)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "GUI resources OK" in completed.stdout