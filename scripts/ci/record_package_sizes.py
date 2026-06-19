#!/usr/bin/env python3
"""Record packaged artifact sizes for CI budgets."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "dist"
BUDGET_MIB = 180


def artifact_size_bytes(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            total += item.stat().st_size
    return total


def main() -> int:
    if not DIST.exists():
        print("No dist/ artifacts found; skipping size report.", file=sys.stderr)
        return 0

    artifacts: list[dict[str, object]] = []
    report: dict[str, object] = {"budget_mib": BUDGET_MIB, "artifacts": artifacts}
    over_budget: list[str] = []
    for path in sorted(DIST.iterdir()):
        size = artifact_size_bytes(path)
        mib = round(size / (1024 * 1024), 2)
        entry: dict[str, object] = {
            "name": path.name,
            "path": str(path.relative_to(ROOT)),
            "bytes": size,
            "mib": mib,
        }
        artifacts.append(entry)
        if mib > BUDGET_MIB:
            over_budget.append(path.name)

    output = ROOT / "dist" / "package-size-report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))

    if over_budget:
        print(
            f"ERROR: Artifacts exceed {BUDGET_MIB} MiB budget: {', '.join(over_budget)}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())