"""Build follow-up pipeline commands from an existing run manifest."""

from __future__ import annotations

import sys
from pathlib import Path

from gui.paths import run_artifacts
from gui.pipeline.adapter import PipelineCommand, orchestrator_script
from gui.pipeline.contracts_bridge import load_run_manifest

GRANULARITY_ORDER = ("coarse", "normal", "fine")


def adjust_granularity(current: str, *, finer: bool) -> str:
    if current not in GRANULARITY_ORDER:
        current = "normal"
    index = GRANULARITY_ORDER.index(current)
    if finer:
        return GRANULARITY_ORDER[min(index + 1, len(GRANULARITY_ORDER) - 1)]
    return GRANULARITY_ORDER[max(index - 1, 0)]


def _append_manifest_options(argv: list[str], manifest: dict[str, object]) -> None:
    options = manifest.get("options")
    if not isinstance(options, dict):
        return
    argv.extend(["--granularity", str(options.get("granularity", "normal"))])
    argv.extend(["--index-language", str(options.get("index_language", "Persian"))])
    argv.extend(["--ocr", str(options.get("ocr", "off"))])
    if options.get("overwrite"):
        argv.append("--overwrite")
    limit = options.get("limit")
    if isinstance(limit, int) and limit > 0:
        argv.extend(["--limit", str(limit)])


def _artifact_paths(run_id: str, manifest: dict[str, object]) -> tuple[Path, Path, Path, Path]:
    artifacts = run_artifacts(run_id)
    paths = manifest.get("paths")
    event_file = artifacts.events
    log_file = artifacts.log
    if isinstance(paths, dict):
        raw_event = paths.get("event_file")
        raw_log = paths.get("log_file")
        if isinstance(raw_event, str) and raw_event:
            event_file = Path(raw_event)
        if isinstance(raw_log, str) and raw_log:
            log_file = Path(raw_log)
    return artifacts.manifest, event_file, log_file, artifacts.stop_file


def build_approve_command(manifest_path: Path) -> PipelineCommand:
    manifest = load_run_manifest(manifest_path)
    run_id = str(manifest["run_id"])
    source = manifest.get("source")
    paths = manifest.get("paths")
    if not isinstance(source, dict) or not isinstance(paths, dict):
        raise ValueError("Run manifest is missing source or paths.")
    work_dir = Path(str(paths["work_dir"]))
    argv: list[str] = [sys.executable, str(orchestrator_script())]
    if source.get("kind") == "pdf":
        argv.append(str(source["path"]))
    argv.extend(
        [
            "--work-dir",
            str(work_dir),
            "--start-at",
            "mindmap",
            "--approve-segmentation",
            "--require-valid-parts",
        ]
    )
    _append_manifest_options(argv, manifest)
    manifest_file, event_file, log_file, stop_file = _artifact_paths(run_id, manifest)
    argv.extend(
        [
            "--event-file",
            str(event_file),
            "--manifest-file",
            str(manifest_file),
            "--log-file",
            str(log_file),
            "--run-id",
            run_id,
            "--stop-file",
            str(stop_file),
        ]
    )
    return PipelineCommand(
        run_id=run_id,
        argv=tuple(argv),
        work_dir=work_dir,
        event_file=event_file,
        manifest_file=manifest_file,
        log_file=log_file,
        stop_file=stop_file,
    )


def build_regenerate_command(manifest_path: Path, *, granularity: str) -> PipelineCommand:
    manifest = load_run_manifest(manifest_path)
    run_id = str(manifest["run_id"])
    source = manifest.get("source")
    paths = manifest.get("paths")
    if not isinstance(source, dict) or not isinstance(paths, dict):
        raise ValueError("Run manifest is missing source or paths.")
    if source.get("kind") != "pdf":
        raise ValueError("Segmentation regeneration requires a PDF source.")
    work_dir = Path(str(paths["work_dir"]))
    argv: list[str] = [
        sys.executable,
        str(orchestrator_script()),
        str(source["path"]),
        "--work-dir",
        str(work_dir),
        "--rerun",
        "segmentation",
        "--granularity",
        granularity,
    ]
    options = manifest.get("options")
    if isinstance(options, dict):
        argv.extend(["--index-language", str(options.get("index_language", "Persian"))])
        argv.extend(["--ocr", str(options.get("ocr", "off"))])
        if options.get("overwrite"):
            argv.append("--overwrite")
    manifest_file, event_file, log_file, stop_file = _artifact_paths(run_id, manifest)
    argv.extend(
        [
            "--event-file",
            str(event_file),
            "--manifest-file",
            str(manifest_file),
            "--log-file",
            str(log_file),
            "--run-id",
            run_id,
            "--stop-file",
            str(stop_file),
        ]
    )
    return PipelineCommand(
        run_id=run_id,
        argv=tuple(argv),
        work_dir=work_dir,
        event_file=event_file,
        manifest_file=manifest_file,
        log_file=log_file,
        stop_file=stop_file,
    )


def build_resume_command(manifest_path: Path) -> PipelineCommand:
    manifest = load_run_manifest(manifest_path)
    run_id = str(manifest["run_id"])
    paths = manifest.get("paths")
    if not isinstance(paths, dict):
        raise ValueError("Run manifest is missing paths.")
    work_dir = Path(str(paths["work_dir"]))
    manifest_file, event_file, log_file, stop_file = _artifact_paths(run_id, manifest)
    return PipelineCommand(
        run_id=run_id,
        argv=(
            sys.executable,
            str(orchestrator_script()),
            "--resume",
            str(manifest_path),
            "--stop-file",
            str(stop_file),
        ),
        work_dir=work_dir,
        event_file=event_file,
        manifest_file=manifest_file,
        log_file=log_file,
        stop_file=stop_file,
    )
