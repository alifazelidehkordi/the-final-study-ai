#!/usr/bin/env python3
"""Fail CI when pyside6-deploy produced no package outputs."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEPLOYMENT = ROOT / "gui" / "deployment"
DIST = ROOT / "dist"

ARTIFACT_MARKERS = (
    DEPLOYMENT / "__main__.dist",
    DEPLOYMENT / "__main__.app",
    DIST,
)


def has_package_output() -> bool:
    for marker in ARTIFACT_MARKERS:
        if not marker.exists():
            continue
        if marker.is_file():
            return True
        if any(marker.rglob("*")):
            return True
    return False


def main() -> int:
    if has_package_output():
        print("Package outputs found.")
        return 0
    print(
        "ERROR: No package outputs under gui/deployment/ or dist/. "
        "pyside6-deploy likely failed silently.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())