from __future__ import annotations

import json
from pathlib import Path

from gui.pipeline.resume_adapter import (
    adjust_granularity,
    build_approve_command,
    build_regenerate_command,
)


def _write_manifest(path: Path, *, granularity: str = "normal") -> None:
    pdf_path = str(path.parent / "book.pdf")
    work_dir = str(path.parent / "book_work")
    path.write_text(
        json.dumps(
            {
                "schema": "final-study.run",
                "version": 1,
                "run_id": "run-42",
                "created_at": "2026-06-19T10:00:00Z",
                "updated_at": "2026-06-19T10:05:00Z",
                "status": "awaiting_review",
                "preset": "complete",
                "source": {"kind": "pdf", "path": pdf_path},
                "paths": {
                    "work_dir": work_dir,
                    "event_file": str(path.parent / "events.jsonl"),
                    "log_file": str(path.parent / "run.log"),
                },
                "options": {
                    "granularity": granularity,
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


def test_adjust_granularity_moves_finer_and_coarser() -> None:
    assert adjust_granularity("normal", finer=True) == "fine"
    assert adjust_granularity("normal", finer=False) == "coarse"


def test_build_approve_command_uses_mindmap_start(tmp_path: Path, monkeypatch) -> None:
    manifest = tmp_path / "run.json"
    _write_manifest(manifest)
    monkeypatch.setattr(
        "gui.pipeline.resume_adapter.run_artifacts",
        lambda run_id: type(
            "Artifacts",
            (),
            {
                "manifest": manifest,
                "events": tmp_path / "events.jsonl",
                "log": tmp_path / "run.log",
                "stop_file": tmp_path / "stop.requested",
            },
        )(),
    )
    command = build_approve_command(manifest)
    assert "--start-at" in command.argv
    assert "mindmap" in command.argv
    assert "--approve-segmentation" in command.argv


def test_build_regenerate_command_reruns_segmentation(tmp_path: Path, monkeypatch) -> None:
    manifest = tmp_path / "run.json"
    _write_manifest(manifest, granularity="normal")
    monkeypatch.setattr(
        "gui.pipeline.resume_adapter.run_artifacts",
        lambda run_id: type(
            "Artifacts",
            (),
            {
                "manifest": manifest,
                "events": tmp_path / "events.jsonl",
                "log": tmp_path / "run.log",
                "stop_file": tmp_path / "stop.requested",
            },
        )(),
    )
    command = build_regenerate_command(manifest, granularity="fine")
    assert "--rerun" in command.argv
    assert "segmentation" in command.argv
    assert "fine" in command.argv