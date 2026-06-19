"""Read versioned pipeline contracts from the orchestrator package."""

from __future__ import annotations

import sys

from gui.paths import project_root

_ROOT = project_root()
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.pipeline_contracts import (  # noqa: E402
    ContractError,
    load_run_manifest,
    read_events,
    validate_run_manifest,
)

__all__ = [
    "ContractError",
    "load_run_manifest",
    "read_events",
    "validate_run_manifest",
]