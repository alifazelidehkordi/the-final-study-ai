"""Build canonical run_pipeline.py argument arrays."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from gui.paths import project_root, run_artifacts
from gui.pipeline.models import RunPreset, RunRequest
from gui.pipeline.validation import resolve_work_dir


@dataclass(frozen=True)
class PipelineCommand:
    run_id: str
    argv: tuple[str, ...]
    work_dir: Path
    event_file: Path
    manifest_file: Path
    log_file: Path
    stop_file: Path


def orchestrator_script() -> Path:
    return project_root() / "scripts" / "run_pipeline.py"


def build_pipeline_command(request: RunRequest, *, run_id: str | None = None) -> PipelineCommand:
    resolved_run_id = run_id or uuid4().hex
    artifacts = run_artifacts(resolved_run_id)
    artifacts.base.mkdir(parents=True, exist_ok=True)
    work_dir = resolve_work_dir(request)
    argv: list[str] = [sys.executable, str(orchestrator_script())]

    if request.preset == RunPreset.MINDMAPS_ONLY:
        argv.extend(
            [
                "--work-dir",
                str(work_dir),
                "--mindmap-only",
                "--require-valid-parts",
            ]
        )
    else:
        pdf = request.pdf_path.expanduser().resolve() if request.pdf_path else None
        if pdf is None:
            raise ValueError("PDF presets require a PDF path.")
        argv.append(str(pdf))
        argv.extend(
            [
                "--work-dir",
                str(work_dir),
                "--granularity",
                request.advanced.granularity,
                "--index-language",
                request.advanced.index_language,
                "--ocr",
                request.advanced.ocr,
            ]
        )
        if request.preset == RunPreset.MARKDOWN_INDEX:
            argv.extend(["--stop-after", "segmentation"])

    if request.advanced.overwrite:
        argv.append("--overwrite")
    if request.advanced.limit is not None:
        argv.extend(["--limit", str(request.advanced.limit)])

    argv.extend(
        [
            "--event-file",
            str(artifacts.events),
            "--manifest-file",
            str(artifacts.manifest),
            "--log-file",
            str(artifacts.log),
            "--run-id",
            resolved_run_id,
            "--stop-file",
            str(artifacts.stop_file),
        ]
    )

    return PipelineCommand(
        run_id=resolved_run_id,
        argv=tuple(argv),
        work_dir=work_dir,
        event_file=artifacts.events,
        manifest_file=artifacts.manifest,
        log_file=artifacts.log,
        stop_file=artifacts.stop_file,
    )