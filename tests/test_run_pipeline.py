from __future__ import annotations

import importlib.util
import json
import stat
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_pipeline.py"
SPEC = importlib.util.spec_from_file_location("run_pipeline", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
pipeline = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = pipeline
SPEC.loader.exec_module(pipeline)


def parse(*arguments: str):
    args = pipeline.build_parser().parse_args(arguments)
    return args, pipeline.normalize_options(args)


def executable_script(path: Path, body: str) -> Path:
    path.write_text("#!/usr/bin/env python3\n" + body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def test_legacy_skip_flags_map_to_canonical_stages() -> None:
    _, options = parse("--skip-convert", "book.pdf")
    assert options.start_at == "segmentation"

    _, options = parse("--skip-convert", "--skip-segment", "book.pdf")
    assert options.start_at == "mindmap"

    _, options = parse("--skip-mindmap", "book.pdf")
    assert options.stop_after == "segmentation"


def test_legacy_skip_segment_keeps_conversion_and_skips_segmentation() -> None:
    _, options = parse("--skip-segment", "book.pdf")
    assert options.start_at == "conversion"
    assert options.skip_segmentation is True


def test_mindmap_command_uses_python_entry_point_and_native_paths(
    tmp_path: Path,
) -> None:
    work = tmp_path / "کار پوشه"
    paths = pipeline.PipelinePaths(
        pdf=None,
        work_dir=work,
        markdown=None,
        parts=work / "parts",
        opml=work / "opml",
        xmind=work / "xmind",
    )
    project = tmp_path / "mind map"
    tooling = pipeline.Tooling(
        pdf_python=tmp_path / "pdf-python",
        pdf_script=tmp_path / "convert.py",
        mindmap_project=project,
        mindmap_python=project / ".venv/Scripts/python.exe",
        mindmap_pipeline=project / "scripts/pipeline.py",
        prompt_file=project / "prompts/prompt.md",
    )
    options = pipeline.PipelineOptions(
        start_at="mindmap",
        stop_after=None,
        skip_segmentation=False,
        approve_segmentation=True,
        overwrite=True,
        granularity="normal",
        index_language="Persian",
        ocr="off",
        limit=3,
    )

    command = pipeline.mindmap_command(paths, tooling, options)

    assert command[:3] == [
        str(tooling.mindmap_python),
        str(tooling.mindmap_pipeline),
        "pdf",
    ]
    assert str(paths.parts) in command
    assert command[-3:] == ["--overwrite", "--limit", "3"]


def test_discover_mindmap_python_uses_available_environment(tmp_path: Path) -> None:
    project = tmp_path / "project"
    legacy = project / ".venv-linux/bin/python"
    portable = project / ".venv/bin/python"
    windows = project / ".venv/Scripts/python.exe"

    legacy.parent.mkdir(parents=True)
    legacy.touch()
    assert pipeline.discover_mindmap_python(project) == legacy

    portable.parent.mkdir(parents=True)
    portable.touch()
    assert pipeline.discover_mindmap_python(project) == portable

    windows.parent.mkdir(parents=True)
    windows.touch()
    assert pipeline.discover_mindmap_python(project) == windows


def test_markdown_and_index_exits_without_review_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pdf = tmp_path / "book.pdf"
    pdf.write_bytes(b"%PDF fixture")
    work = tmp_path / "کتاب work"
    converter = executable_script(
        tmp_path / "convert.py",
        "from pathlib import Path\n"
        "import sys\n"
        "output = Path(sys.argv[sys.argv.index('--output') + 1])\n"
        "output.write_text('<!-- Page 1 -->\\n## Topic\\nBody\\n', encoding='utf-8')\n",
    )
    segmenter = executable_script(
        tmp_path / "segment.py",
        "from pathlib import Path\n"
        "import sys\n"
        "work = Path(sys.argv[sys.argv.index('--output-dir') + 1])\n"
        "(work / 'parts').mkdir(parents=True, exist_ok=True)\n"
        "(work / 'parts' / '01_Topic.md').write_text('## Topic', encoding='utf-8')\n"
        "(work / 'STUDY_INDEX.md').write_text('# Index', encoding='utf-8')\n"
        "(work / 'SEGMENTATION_PREVIEW.md').write_text('# Preview', encoding='utf-8')\n",
    )
    events = tmp_path / "events.jsonl"
    monkeypatch.setenv("PDF_TO_MD_PY", sys.executable)
    monkeypatch.setenv("PDF_TO_MD_SCRIPT", str(converter))
    monkeypatch.setattr(pipeline, "SEGMENT_SCRIPT", segmenter)

    code = pipeline.main(
        (
            str(pdf),
            "--work-dir",
            str(work),
            "--stop-after",
            "segmentation",
            "--event-file",
            str(events),
        )
    )

    assert code == pipeline.EXIT_SUCCESS
    event_types = [json.loads(line)["type"] for line in events.read_text().splitlines()]
    assert "review.required" not in event_types
    assert event_types[-1] == "run.completed"


def test_complete_pipeline_returns_review_exit_and_event(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pdf = tmp_path / "book.pdf"
    pdf.write_bytes(b"%PDF fixture")
    pdf.with_suffix(".md").write_text(
        "<!-- Page 1 -->\n## Topic\n",
        encoding="utf-8",
    )
    work = tmp_path / "کتاب work"
    segmenter = executable_script(
        tmp_path / "segment.py",
        "from pathlib import Path\n"
        "import sys\n"
        "work = Path(sys.argv[sys.argv.index('--output-dir') + 1])\n"
        "(work / 'parts').mkdir(parents=True, exist_ok=True)\n"
        "(work / 'SEGMENTATION_PREVIEW.md').write_text('# Preview', encoding='utf-8')\n",
    )
    events = tmp_path / "events.jsonl"
    monkeypatch.setattr(pipeline, "SEGMENT_SCRIPT", segmenter)

    code = pipeline.main(
        (
            str(pdf),
            "--work-dir",
            str(work),
            "--skip-convert",
            "--event-file",
            str(events),
        )
    )

    assert code == pipeline.EXIT_REVIEW_REQUIRED
    payloads = [json.loads(line) for line in events.read_text().splitlines()]
    assert payloads[-1]["type"] == "review.required"
    assert [payload["seq"] for payload in payloads] == list(
        range(1, len(payloads) + 1)
    )


def test_wrapper_help_delegates_to_python() -> None:
    result = subprocess.run(
        [str(ROOT / "scripts/run_pipeline.sh"), "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "--event-file" in result.stdout
