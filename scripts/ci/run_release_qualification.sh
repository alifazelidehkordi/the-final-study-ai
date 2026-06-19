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

echo "=== Release qualification ($(date -u +%Y-%m-%dT%H:%MZ)) ==="
echo "Platform: $(uname -s) $(uname -m)"
echo "Python: $("$PYTHON" --version)"
echo "Session: DISPLAY=${DISPLAY:-} WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-} XDG_SESSION_TYPE=${XDG_SESSION_TYPE:-}"
echo

bash scripts/ci/run_quality_gates.sh

echo
echo "=== CLI regression suite ==="
"$PYTHON" -m pytest \
  tests/test_run_pipeline.py \
  tests/test_mindmap_integration.py \
  tests/test_pipeline_contracts.py \
  tests/test_artifact_validators.py \
  tests/test_segmentation_contracts.py

echo
echo "=== Qualification summary ==="
"$PYTHON" -m pytest --collect-only -q | tail -1 || true
echo "Release qualification PASSED"