#!/usr/bin/env python3
"""Cross-platform orchestrator for the Final Study AI pipeline."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import IO, Any
from uuid import uuid4

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.pipeline_contracts import (  # noqa: E402
    EventWriter,
    new_run_manifest,
    save_run_manifest,
    set_run_status,
)

EXIT_SUCCESS = 0
EXIT_FATAL = 1
EXIT_PARTIAL = 2
EXIT_REVIEW_REQUIRED = 20

STAGES = ("conversion", "segmentation", "mindmap")
SEGMENT_SCRIPT = ROOT / "scripts" / "segment_markdown_study_parts.py"


class PipelineError(RuntimeError):
    """Expected pipeline configuration or execution failure."""


@dataclass(frozen=True)
class PipelinePaths:
    pdf: Path | None
    work_dir: Path
    markdown: Path | None
    parts: Path
    opml: Path
    xmind: Path


@dataclass(frozen=True)
class Tooling:
    pdf_python: Path
    pdf_script: Path
    mindmap_project: Path
    mindmap_python: Path
    mindmap_pipeline: Path
    prompt_file: Path


@dataclass(frozen=True)
class PipelineOptions:
    start_at: str
    stop_after: str | None
    skip_segmentation: bool
    require_valid_parts: bool
    approve_segmentation: bool
    overwrite: bool
    granularity: str
    index_language: str
    ocr: str
    limit: int | None


class HumanLog:
    """Write human output to the terminal and an optional log file."""

    def __init__(self, path: Path | None) -> None:
        self.path = path
        self._stream: IO[str] | None = None

    def __enter__(self) -> HumanLog:
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._stream = self.path.open("a", encoding="utf-8")
            self.line(f"=== LOG START {datetime.now(timezone.utc).isoformat()} ===")
        return self

    def __exit__(self, *_: object) -> None:
        if self._stream is not None:
            self._stream.close()

    def line(self, text: str = "", *, error: bool = False) -> None:
        print(text, file=sys.stderr if error else sys.stdout, flush=True)
        if self._stream is not None:
            self._stream.write(text + "\n")
            self._stream.flush()

    def run(self, command: Sequence[str], *, cwd: Path | None = None) -> int:
        self.line(f"$ {render_command(command)}")
        process = subprocess.Popen(  # noqa: S603
            list(command),
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if process.stdout is None:
            process.kill()
            raise PipelineError("Could not capture child process output.")
        for line in process.stdout:
            self.line(line.rstrip("\n"))
        return process.wait()


def render_command(command: Sequence[str]) -> str:
    """Render a command for diagnostics, never for execution."""
    return " ".join(
        json.dumps(value) if any(character.isspace() for character in value) else value
        for value in command
    )


def positive_integer(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="PDF -> Markdown -> study parts/index -> OPML -> XMind",
    )
    parser.add_argument("pdf", nargs="?", type=Path, help="source PDF")
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--event-file", type=Path)
    parser.add_argument("--manifest-file", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--log-file", type=Path)

    parser.add_argument("--start-at", choices=STAGES, default="conversion")
    parser.add_argument("--stop-after", choices=STAGES)
    parser.add_argument("--rerun", choices=STAGES)
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--require-valid-parts", action="store_true")
    parser.add_argument("--retry-failed", action="store_true")

    parser.add_argument(
        "--granularity",
        choices=("fine", "normal", "coarse"),
        default="normal",
    )
    parser.add_argument(
        "--index-language",
        "--language",
        dest="index_language",
        default="Persian",
    )
    parser.add_argument("--ocr", choices=("auto", "off"), default="off")
    parser.add_argument("--limit", type=positive_integer)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--approve-segmentation",
        "--approve-segment",
        action="store_true",
    )

    parser.add_argument("--skip-convert", action="store_true")
    parser.add_argument("--skip-segment", action="store_true")
    parser.add_argument("--skip-mindmap", action="store_true")
    parser.add_argument("--mindmap-only", action="store_true")
    return parser


def normalize_options(args: argparse.Namespace) -> PipelineOptions:
    if args.resume is not None:
        raise PipelineError("--resume requires Run Manifest v1; it is not implemented yet.")
    if args.retry_failed:
        raise PipelineError("--retry-failed requires Run Manifest v1.")

    start_at = args.rerun or args.start_at
    stop_after = args.stop_after

    if args.mindmap_only or (args.skip_convert and args.skip_segment):
        start_at = "mindmap"
    elif args.skip_convert:
        start_at = "segmentation"
    if args.skip_mindmap:
        stop_after = "segmentation"
    if stop_after is not None and STAGES.index(start_at) > STAGES.index(stop_after):
        raise PipelineError("--stop-after cannot precede --start-at.")

    return PipelineOptions(
        start_at=start_at,
        stop_after=stop_after,
        skip_segmentation=args.skip_segment,
        require_valid_parts=args.require_valid_parts,
        approve_segmentation=args.approve_segmentation,
        overwrite=args.overwrite,
        granularity=args.granularity,
        index_language=args.index_language,
        ocr=args.ocr,
        limit=args.limit,
    )


def resolve_paths(args: argparse.Namespace, options: PipelineOptions) -> PipelinePaths:
    pdf = args.pdf.expanduser().resolve() if args.pdf is not None else None
    if pdf is not None and (not pdf.is_file() or pdf.suffix.lower() != ".pdf"):
        raise PipelineError(f"PDF not found or invalid: {pdf}")
    if options.start_at != "mindmap" and pdf is None:
        raise PipelineError("A PDF path is required unless starting at mindmap.")

    if args.work_dir is not None:
        work_dir = args.work_dir.expanduser().resolve()
    elif pdf is not None:
        work_dir = pdf.with_name(f"{pdf.stem}_work")
    else:
        raise PipelineError("--work-dir is required for Mind Maps Only.")

    work_dir.mkdir(parents=True, exist_ok=True)
    markdown = pdf.with_suffix(".md") if pdf is not None else None
    return PipelinePaths(
        pdf=pdf,
        work_dir=work_dir,
        markdown=markdown,
        parts=work_dir / "parts",
        opml=work_dir / "opml",
        xmind=work_dir / "xmind",
    )


def discover_mindmap_python(project: Path) -> Path:
    candidates = (
        project / ".venv/Scripts/python.exe",
        project / ".venv/bin/python",
        project / ".venv-linux/bin/python",
    )
    return next((candidate for candidate in candidates if candidate.is_file()), candidates[0])


def discover_tooling() -> Tooling:
    home = Path.home()
    pdf_python = Path(
        os.environ.get(
            "PDF_TO_MD_PY",
            str(home / ".grok/skills/pdf-to-markdown/.venv/bin/python"),
        )
    ).expanduser()
    pdf_script = Path(
        os.environ.get(
            "PDF_TO_MD_SCRIPT",
            str(home / ".grok/skills/pdf-to-markdown/scripts/convert_pdf.py"),
        )
    ).expanduser()
    mindmap_project = Path(
        os.environ.get(
            "MINDMAP_PROJECT",
            str(home / "projects/chatgpt-mindmap-to-xmind"),
        )
    ).expanduser()
    prompt_file = Path(
        os.environ.get(
            "PROMPT_FILE",
            str(mindmap_project / "prompts/prompt-mind-map.md"),
        )
    ).expanduser()
    return Tooling(
        pdf_python=pdf_python,
        pdf_script=pdf_script,
        mindmap_project=mindmap_project,
        mindmap_python=discover_mindmap_python(mindmap_project),
        mindmap_pipeline=mindmap_project / "scripts/pipeline.py",
        prompt_file=prompt_file,
    )


def conversion_command(
    paths: PipelinePaths,
    tooling: Tooling,
    options: PipelineOptions,
) -> list[str]:
    pdf, markdown = require_pdf_paths(paths)
    command = [
        str(tooling.pdf_python),
        str(tooling.pdf_script),
        str(pdf),
        "--output",
        str(markdown),
    ]
    if options.ocr == "off":
        command.append("--no-ocr")
    if options.overwrite:
        command.append("--overwrite")
    return command


def segmentation_command(
    paths: PipelinePaths,
    options: PipelineOptions,
    *,
    event_path: Path | None = None,
    run_id: str | None = None,
) -> list[str]:
    pdf, markdown = require_pdf_paths(paths)
    command = [
        sys.executable,
        str(SEGMENT_SCRIPT),
        "--input",
        str(markdown),
        "--output-dir",
        str(paths.work_dir),
        "--source-pdf",
        str(pdf),
        "--language",
        options.index_language,
        "--granularity",
        options.granularity,
    ]
    if event_path is not None:
        command.extend(("--event-file", str(event_path)))
    if run_id is not None:
        command.extend(("--run-id", run_id))
    return command


def mindmap_command(
    paths: PipelinePaths,
    tooling: Tooling,
    options: PipelineOptions,
) -> list[str]:
    command = [
        str(tooling.mindmap_python),
        str(tooling.mindmap_pipeline),
        "pdf",
        "--input-dir",
        str(paths.parts),
        "--opml-dir",
        str(paths.opml),
        "--xmind-dir",
        str(paths.xmind),
        "--prompt",
        str(tooling.prompt_file),
    ]
    if options.overwrite:
        command.append("--overwrite")
    if options.limit is not None:
        command.extend(("--limit", str(options.limit)))
    return command


def require_file(path: Path, description: str) -> None:
    if not path.is_file():
        raise PipelineError(f"{description} not found: {path}")


def require_pdf_paths(paths: PipelinePaths) -> tuple[Path, Path]:
    if paths.pdf is None or paths.markdown is None:
        raise PipelineError("This stage requires a PDF source and Markdown path.")
    return paths.pdf, paths.markdown


def require_dir(path: Path, description: str) -> None:
    if not path.is_dir():
        raise PipelineError(f"{description} not found: {path}")


def run_stage(
    stage: str,
    label: str,
    command: Sequence[str],
    log: HumanLog,
    events: EventWriter,
    *,
    cwd: Path | None = None,
) -> int:
    log.line(f"=== {label} ===")
    events.emit("stage.started", stage)
    code = log.run(command, cwd=cwd)
    if code == EXIT_SUCCESS:
        events.emit("stage.completed", stage)
    else:
        events.emit("stage.failed", stage, exit_code=code)
    log.line()
    return code


def execute(
    paths: PipelinePaths,
    tooling: Tooling,
    options: PipelineOptions,
    log: HumanLog,
    events: EventWriter,
) -> int:
    events.emit("run.started", "preflight")
    log.line("=== PDF Fidelity Mind Map Pipeline ===")
    log.line(f"PDF       : {paths.pdf or 'existing work directory'}")
    log.line(f"Work dir  : {paths.work_dir}")
    log.line()

    start_index = STAGES.index(options.start_at)
    if start_index <= STAGES.index("conversion"):
        require_file(tooling.pdf_python, "PDF conversion Python")
        require_file(tooling.pdf_script, "PDF conversion script")
        code = run_stage(
            "pdf_to_markdown",
            "Step 1/3: PDF -> Markdown",
            conversion_command(paths, tooling, options),
            log,
            events,
        )
        if code != EXIT_SUCCESS:
            return EXIT_FATAL
    else:
        if options.start_at == "segmentation":
            _, markdown = require_pdf_paths(paths)
            require_file(markdown, "Existing Markdown")
        log.line("=== Step 1/3: skipped ===")
        log.line()

    if options.stop_after == "conversion":
        events.emit("run.completed", "finalize")
        return EXIT_SUCCESS

    segmentation_ran = (
        start_index <= STAGES.index("segmentation") and not options.skip_segmentation
    )
    if segmentation_ran:
        code = run_stage(
            "segmentation",
            "Step 2/3: Markdown -> study parts + index",
            segmentation_command(
                paths,
                options,
                event_path=events.path,
                run_id=events.run_id,
            ),
            log,
            events,
        )
        if code != EXIT_SUCCESS:
            return EXIT_FATAL
    else:
        require_dir(paths.parts, "Study parts")
        log.line(f"=== Step 2/3: skipped (using {paths.parts}) ===")
        log.line()

    if options.stop_after == "segmentation":
        events.emit("run.completed", "finalize")
        return EXIT_SUCCESS

    if segmentation_ran and not options.approve_segmentation:
        log.line("=== Segmentation review required ===")
        log.line(f"Read {paths.work_dir / 'SEGMENTATION_PREVIEW.md'} and STUDY_INDEX.md")
        events.emit("review.required", "review", work_dir=str(paths.work_dir))
        return EXIT_REVIEW_REQUIRED

    require_dir(paths.parts, "Study parts")
    if options.require_valid_parts:
        from scripts.artifact_validators import (
            ArtifactValidationError,
            validate_parts_manifest,
        )

        try:
            validate_parts_manifest(paths.work_dir / "parts-manifest.json")
        except ArtifactValidationError as exc:
            raise PipelineError(str(exc)) from exc
    require_dir(tooling.mindmap_project, "Mind-map project")
    require_file(tooling.mindmap_python, "Mind-map Python")
    require_file(tooling.mindmap_pipeline, "Mind-map pipeline")
    require_file(tooling.prompt_file, "Mind-map prompt")
    code = run_stage(
        "mindmap_opml",
        "Step 3/3: Study parts -> OPML -> XMind",
        mindmap_command(paths, tooling, options),
        log,
        events,
        cwd=tooling.mindmap_project,
    )
    if code not in (EXIT_SUCCESS, EXIT_PARTIAL):
        return EXIT_FATAL

    events.emit("run.completed", "finalize", partial=code == EXIT_PARTIAL)
    log.line("Done.")
    log.line(f"Study index : {paths.work_dir / 'STUDY_INDEX.md'}")
    log.line(f"Index PDF   : {paths.work_dir / 'STUDY_INDEX.pdf'}")
    log.line(f"Study parts : {paths.parts}")
    log.line(f"XMind files : {paths.xmind}")
    return code


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_id = args.run_id or uuid4().hex
    event_path = args.event_file.expanduser().resolve() if args.event_file else None
    events = EventWriter(event_path, run_id)
    manifest_path: Path | None = None
    manifest: dict[str, Any] | None = None

    try:
        options = normalize_options(args)
        paths = resolve_paths(args, options)
        tooling = discover_tooling()
        log_path = args.log_file.expanduser().resolve() if args.log_file else None
        if args.manifest_file is not None:
            manifest_path = args.manifest_file.expanduser().resolve()
            preset = (
                "mindmaps_only"
                if options.start_at == "mindmap"
                else "markdown_index"
                if options.stop_after == "segmentation"
                else "complete"
            )
            manifest = new_run_manifest(
                run_id=run_id,
                preset=preset,
                source={
                    "kind": "work_dir" if paths.pdf is None else "pdf",
                    "path": str(paths.work_dir if paths.pdf is None else paths.pdf),
                },
                paths={
                    "work_dir": str(paths.work_dir),
                    "event_file": str(event_path) if event_path else "",
                    "log_file": str(log_path) if log_path else "",
                },
                options={
                    "granularity": options.granularity,
                    "ocr": options.ocr,
                    "index_language": options.index_language,
                    "overwrite": options.overwrite,
                    "limit": options.limit,
                },
            )
            save_run_manifest(manifest_path, manifest)
            set_run_status(manifest_path, manifest, "running")
        with HumanLog(log_path) as log:
            code = execute(paths, tooling, options, log, events)
            if manifest_path is not None and manifest is not None:
                status = {
                    EXIT_SUCCESS: "completed",
                    EXIT_PARTIAL: "partial",
                    EXIT_REVIEW_REQUIRED: "awaiting_review",
                }.get(code, "failed")
                set_run_status(manifest_path, manifest, status)
            if code not in (EXIT_SUCCESS, EXIT_PARTIAL, EXIT_REVIEW_REQUIRED):
                events.emit("run.failed", "finalize", exit_code=code)
            return code
    except PipelineError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        events.emit("run.failed", "preflight", error=str(exc))
        if manifest_path is not None and manifest is not None:
            set_run_status(
                manifest_path,
                manifest,
                "failed",
                last_error={"code": "E_CHILD_PROCESS", "detail": str(exc)},
            )
        return EXIT_FATAL
    except KeyboardInterrupt:
        print("ERROR: interrupted.", file=sys.stderr)
        events.emit("run.stopped", "finalize")
        return EXIT_FATAL


if __name__ == "__main__":
    raise SystemExit(main())
