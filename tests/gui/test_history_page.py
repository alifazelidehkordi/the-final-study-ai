from __future__ import annotations

import json
from pathlib import Path

from gui.tokens import LIGHT_COLORS
from gui.widgets.history_page import HistoryPage


def _write_run(run_dir: Path) -> None:
    run_dir.mkdir(parents=True)
    pdf_path = str(run_dir / "book.pdf")
    work_dir = str(run_dir / "book_work")
    (run_dir / "run.json").write_text(
        json.dumps(
            {
                "schema": "final-study.run",
                "version": 1,
                "run_id": run_dir.name,
                "created_at": "2026-06-19T10:00:00Z",
                "updated_at": "2026-06-19T10:00:00Z",
                "status": "completed",
                "preset": "markdown_index",
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


def test_history_page_lists_runs(qtbot, qapp, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("gui.pipeline.run_store.runs_dir", lambda: tmp_path)
    _write_run(tmp_path / "run-a")
    page = HistoryPage(LIGHT_COLORS)
    qtbot.addWidget(page)
    page.refresh_runs()
    assert page._runs.count() == 1