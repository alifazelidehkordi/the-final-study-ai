#!/usr/bin/env python3
"""Verify packaged GUI resources required at runtime."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gui.i18n import translation_file
from gui.paths import compatibility_manifest_path
from gui.settings import LocaleCode


def main() -> int:
    errors: list[str] = []

    persian_qm = translation_file(LocaleCode.FA)
    if not persian_qm.is_file() or persian_qm.stat().st_size == 0:
        errors.append(f"Missing or empty translation file: {persian_qm}")

    manifest_path = compatibility_manifest_path()
    if not manifest_path.is_file():
        errors.append(f"Missing compatibility manifest: {manifest_path}")
    else:
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"Compatibility manifest is invalid JSON: {exc}")
        else:
            if payload.get("schema") != "final-study.compatibility":
                errors.append("Compatibility manifest schema mismatch.")

    schemas = [
        ROOT / "schemas" / "compatibility-manifest-v1.json",
        ROOT / "schemas" / "event-v1.schema.json",
        ROOT / "schemas" / "run-manifest-v1.schema.json",
        ROOT / "schemas" / "parts-manifest-v1.schema.json",
    ]
    for schema_path in schemas:
        if not schema_path.is_file():
            errors.append(f"Missing schema: {schema_path}")

    if errors:
        for message in errors:
            print(f"ERROR: {message}", file=sys.stderr)
        return 1

    print("GUI resources OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())