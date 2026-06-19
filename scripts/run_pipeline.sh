#!/usr/bin/env bash
# Compatibility wrapper. The cross-platform implementation lives in Python.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="${PIPELINE_PYTHON:-python3}"

exec "${PYTHON}" "${SCRIPT_DIR}/run_pipeline.py" "$@"
