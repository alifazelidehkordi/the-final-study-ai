from __future__ import annotations

import json
from pathlib import Path

from gui.pipeline.run_store import list_runs


def _write_run(run_dir: Path, run_id: str, *, updated_at: str) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = str(run_dir.parent / f"{run_id}.pdf")
    work_dir = str(run_dir.parent / f"{run_id}_work")
    (run_dir / "run.json").write_text(
        json.dumps(
            {
                "schema": "final-study.run",
                "version": 1,
                "run_id": run_id,
                "created_at": updated_at,
                "updated_at": updated_at,
                "status": "completed",
                "preset": "complete",
                "source": {"kind": "pdf", "path": pdf_path},
                "paths": {
                    "work_dir": work_dir,
                    "event_file": "",
                    "log_file": "",
                },
                "options": {
                    "granularity": "normal",
                    "ocr": "off",
                    "index_language": "Persian",
                    "overwrite": False,
                    "limit": None,
                },
                "tool_versions": {},
                "stages": {},
                "items": {},
                "artifacts": [],
                "last_error": None,
            }
        ),
        encoding="utf-8",
    )


def test_list_runs_sorts_by_updated_at(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("gui.pipeline.run_store.runs_dir", lambda: tmp_path)
    _write_run(tmp_path / "older", "older", updated_at="2026-06-19T10:00:00Z")
    _write_run(tmp_path / "newer", "newer", updated_at="2026-06-19T12:00:00Z")
    summaries = list_runs()
    assert [summary.run_id for summary in summaries] == ["newer", "older"]