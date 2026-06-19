#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
elif [[ -n "${PYTHON:-}" ]]; then
  PYTHON="$PYTHON"
else
  PYTHON="python3"
fi

"$PYTHON" -m ruff check .
"$PYTHON" -m mypy
"$PYTHON" -m pytest
"$PYTHON" -m bandit -q -r gui scripts/chatgpt_login_probe.py -ll
"$PYTHON" scripts/ci/validate_gui_resources.py
"$PYTHON" scripts/ci/gui_launch_smoke.py